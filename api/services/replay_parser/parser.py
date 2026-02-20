import os
import mpyq
import hashlib
import json
import unicodedata
from datetime import datetime, timezone
from api.logger import ColoredLogger

from .utils import setup_imp_shim, get_hero_display_name, clean_text
# CRITICAL: Setup shim before importing heroprotocol on Python 3.12+
setup_imp_shim()
from heroprotocol.versions import latest

from .talents import load_talent_data, get_talent_from_index, TALENTS_DB
from .header import get_match_id
from .tracker import process_tracker_events, process_game_events

# Increment when parser logic changes
PARSER_VERSION = "3.5" 

def parse_replay(replay_path, options=None):
    setup_imp_shim()
    load_talent_data()

    if not os.path.exists(replay_path):
        return {"status": "error", "message": "File not found"}

    try:
        archive = mpyq.MPQArchive(replay_path)
        protocol = latest()
        
        # 1. Header & ID
        header_content = archive.header['user_data_header']['content']
        header = protocol.decode_replay_header(header_content)
        match_id = get_match_id(replay_path)
        
        game_loops = header.get('m_elapsedGameLoops', 0)
        game_duration_seconds = game_loops / 16.0
        time_played_str = f"{int(game_duration_seconds // 60)}:{int(game_duration_seconds % 60):02d}"
        
        # Time Calibration
        time_utc = header.get('m_timeUTC', 0)
        if time_utc and time_utc > 0:
            unix_ts = (time_utc - 116444736000000000) / 10000000
            timestamp_iso = datetime.fromtimestamp(unix_ts, tz=timezone.utc).isoformat()
        else:
            # Fallback: Extract from filename (e.g., "2025-12-25 05.45.56 Battlefield of Eternity.StormReplay")
            import re
            filename = os.path.basename(replay_path)
            match = re.search(r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2})\.(\d{2})\.(\d{2})', filename)
            if match:
                year, month, day, hour, minute, second = match.groups()
                match_datetime = datetime(int(year), int(month), int(day), 
                                         int(hour), int(minute), int(second), 
                                         tzinfo=timezone.utc)
                timestamp_iso = match_datetime.isoformat()
            else:
                # Last resort: use file modification time
                import pathlib
                mtime = pathlib.Path(replay_path).stat().st_mtime
                timestamp_iso = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()

        
        # 2. Details
        details = protocol.decode_replay_details(archive.read_file('replay.details'))
        map_name = details.get('m_title', b'').decode('utf-8')
        
        players = []
        winning_team = None
        for p in details['m_playerList']:
            # Robust integer conversion for result (1=Win, 2=Loss)
            result = int(p['m_result'])
            if result == 1: winning_team = p['m_teamId']
            
            h_raw = p['m_hero'].decode('utf-8')
            p_name = p['m_name'].decode('utf-8')
            
            # toon mapping for unique ID: region-realm-id
            toon = p.get('m_toon', {})
            t_handle = f"{toon.get('m_region', 0)}-{toon.get('m_realm', 0)}-{toon.get('m_id', 0)}"
            
            # Debug log for critical user
            if 'Discerning' in p_name:
                pass # ColoredLogger.info(f"DEBUG: Discerning Result: {result}", "PARSER")

            players.append({
                'name': p_name,
                'toon_handle': t_handle,
                'hero': get_hero_display_name(h_raw),
                'team': p['m_teamId'],
                'win': (result == 1),
                'hero_level': p.get('m_heroLevel', 0),
                'account_level': p.get('m_playerLevel', 0),
                '_working_set_slot_id': p.get('m_workingSetSlotId'),
            })

        # 2.5 Tracker Events (includes picks from SHeroPickedEvent)
        tracker_events = protocol.decode_replay_tracker_events(archive.read_file('replay.tracker.events'))
        stats_containers = {i: {'stats': {}, 'talents': []} for i in range(1, 11)}
        stats_data, bans, tracker_picks = process_tracker_events(tracker_events, players, stats_containers, game_loops)

        # 2.6 Pick order: prefer SHeroPickedEvent (true draft order), then initData, then roster
        picks = []
        if len(tracker_picks) >= 10:
            picks = tracker_picks
        else:
            try:
                init_data = protocol.decode_replay_initdata(archive.read_file('replay.initData'))
                sync = init_data.get('m_syncLobbyState') or {}
                lobby_state = sync.get('m_lobbyState') if isinstance(sync, dict) else {}
                slots = (lobby_state.get('m_slots') if isinstance(lobby_state, dict) else []) or []
                if not slots and isinstance(sync, dict):
                    slots = sync.get('m_slots') or []
                gd = sync.get('m_gameDescription') if isinstance(sync, dict) else {}
                if not slots and isinstance(gd, dict):
                    slots = (gd.get('m_lobbyState') or {}).get('m_slots') or gd.get('m_slots') or []
                slots = (slots or [])[:10]
                hero_to_players = {}
                for p in players:
                    h = clean_text(p.get('hero') or '')
                    if h:
                        hero_to_players.setdefault(h, []).append(p)
                for slot_index, slot in enumerate(slots):
                    if not isinstance(slot, dict):
                        continue
                    h_raw = slot.get('m_hero') or b''
                    hero_raw = h_raw.decode('utf-8') if isinstance(h_raw, bytes) else str(h_raw)
                    hero_display = get_hero_display_name(hero_raw)
                    key = clean_text(hero_display or '')
                    cands = hero_to_players.get(key, [])
                    if not cands and key:
                        cands = hero_to_players.get(hero_raw.lower().replace(' ', '').replace('-', '').replace("'", ''), [])
                    pl = next((c for c in cands if clean_text(c.get('hero') or '') == key), cands[0] if cands else None)
                    if pl:
                        picks.append({'order': slot_index + 1, 'hero': pl['hero'], 'team': pl['team'], 'name': pl['name']})
            except Exception as e:
                ColoredLogger.warn(f"initData picks extraction failed: {e}", "PARSER")
        if not picks and players:
            for order, pl in enumerate(players, 1):
                picks.append({'order': order, 'hero': pl['hero'], 'team': pl['team'], 'name': pl['name']})

        # 3. Game Events (Backup for talents, Stitches Hooks, DC detection)
        try:
            game_events_list = list(protocol.decode_replay_game_events(archive.read_file('replay.game.events')))
            stats_data = process_game_events(game_events_list, players, stats_data, game_loops)
        except Exception as e:
            ColoredLogger.warn(f"Game events decode/process failed: {e}", "PARSER")
        
        # 4. Normalization & User Detection
        for i, p in enumerate(players):
            pid = i + 1
            src = stats_data.get(pid, {'stats': {}, 'talents': []})
            p['stats'] = src['stats']
            p['talents'] = src['talents']
            p['death_timestamps'] = src.get('death_timestamps', [])
            p['disconnected'] = src.get('disconnected', False)
            if p['disconnected']:
                p['dc_gameloop'] = src.get('dc_gameloop')
                p['dc_timestamp'] = src.get('dc_timestamp')

            
            # Map stats for frontend
            s = p['stats']
            p['kv_stats'] = {
                'Takedowns': s.get('Takedowns', 0),
                'Deaths': s.get('Deaths', 0),
                'HeroDamage': s.get('HeroDamage', 0),
                'Healing': s.get('Healing', 0),
                'XP': s.get('ExperienceContribution', 0)
            }
            
            # Stitches Hook Injection
            if 'Stitches' in p['hero'] and 'HooksThrown' in src.get('specific_stats', {}):
                 hooks_val = src['specific_stats']['HooksThrown']
                 p['stats']['HooksThrown'] = hooks_val
                 p['kv_stats']['HooksThrown'] = hooks_val

        # Mass-leave safeguard: if 4+ players marked DC, treat as end-of-game (everyone leaves)
        dc_count = sum(1 for p in players if p.get('disconnected'))
        if dc_count >= 4:
            for p in players:
                p['disconnected'] = False
                p.pop('dc_gameloop', None)
                p.pop('dc_timestamp', None)

        # 4.5 Team Level Milestones (L10/L20) derived from talent timestamps
        # Uses the 4th and 7th picked talents (after sorting by timestamp).
        team_level_milestones = {0: {10: None, 20: None}, 1: {10: None, 20: None}}
        for p in players:
            team_id = p.get('team')
            if team_id not in team_level_milestones:
                continue
            t = sorted((p.get('talents') or []), key=lambda x: x.get('timestamp') or 0)
            if len(t) >= 4:
                ts10 = t[3].get('timestamp')
                if ts10 and ts10 > 60:
                    cur = team_level_milestones[team_id][10]
                    if cur is None or ts10 < cur:
                        team_level_milestones[team_id][10] = ts10
            if len(t) >= 7:
                ts20 = t[6].get('timestamp')
                if ts20 and ts20 > 120:
                    cur = team_level_milestones[team_id][20]
                    if cur is None or ts20 < cur:
                        team_level_milestones[team_id][20] = ts20

        # User detection (More robust: prioritize specific IDs over generic 'Player')
        known_identifiers = ['discerning', 'cerebrate', 'ozyroth'] 
        user_name_env = os.environ.get('PLAYER_NAME', '').lower()
        if user_name_env and user_name_env != 'player':
            known_identifiers.insert(0, user_name_env)

        user_player = None
        # First pass: Look for high-confidence specific IDs
        for p in players:
            p_name_low = p['name'].lower()
            if any(ident in p_name_low for ident in known_identifiers):
                user_player = p
                break
        
        # Second pass: Fallback to 'Player' if still not found
        if not user_player:
            for p in players:
                if 'player' in p['name'].lower():
                    user_player = p
                    break
        
        if not user_player: user_player = players[0]
        user_won = winning_team == user_player['team']

        return {
            "status": "success",
            "match_id": match_id,
            "map": map_name,
            "game_length": int(game_duration_seconds),
            "timestamp_iso": timestamp_iso,
            "result": "WIN" if user_won else "LOSS",
            "hero": user_player['hero'],
            "players": players,
            "user_name": user_player['name'],
            "user_toon_handle": user_player['toon_handle'],
            "parser_version": PARSER_VERSION,
            "advanced_stats": {
                "bans": bans,
                "picks": picks,
                "level_milestones": team_level_milestones,
                "structure_destructions": stats_data.get('structure_destructions', []),
                "merc_captures": stats_data.get('merc_captures', []),
                "boss_captures": stats_data.get('boss_captures', []),
                "player_deaths": stats_data.get('player_deaths', [])
            }
        }

    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}
