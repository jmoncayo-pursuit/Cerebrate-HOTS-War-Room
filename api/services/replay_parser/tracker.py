import unicodedata
from . import talents
from .talents import get_talent_from_index
from .utils import get_hero_display_name, clean_text

def process_tracker_events(events, players, stats_data):
    """
    Process all tracker events to extract KDA, Hero Stats, Talents, and map-specific metrics.
    """
    unit_tags = {}
    active_boss_engagements = {}
    bans = []
    
    # Trackers for map events (shared across players or specific to the archive)
    if 'merc_captures' not in stats_data: stats_data['merc_captures'] = []
    if 'structure_destructions' not in stats_data: stats_data['structure_destructions'] = []
    if 'boss_captures' not in stats_data: stats_data['boss_captures'] = []
    if 'objective_events' not in stats_data: stats_data['objective_events'] = []
    if 'player_deaths' not in stats_data: stats_data['player_deaths'] = []

    for event in events:
        etype = event['_event']
        if '.' in etype: etype = etype.split('.')[-1]
        gameloop = event['_gameloop']
        
        # --- UNIT TRACKING ---
        if etype == 'SUnitBornEvent':
            tag = event.get('m_unitTagIndex')
            if tag is not None:
                u_type = event.get('m_unitTypeName', b'').decode('utf-8') if isinstance(event.get('m_unitTypeName'), bytes) else str(event.get('m_unitTypeName', ''))
                u_pid = event.get('m_controlPlayerId', event.get('m_upkeepPlayerId'))
                unit_tags[tag] = {'type': u_type, 'pid': u_pid}
                
                # Boss spawn detection
                boss_keywords = ['Boss', 'GraveyardBoss', 'ArchangelSiege', 'WebweaverQueen', 'SlimeBoss']
                if any(kw in u_type for kw in boss_keywords) and u_pid is None:
                    unit_tags[tag]['is_boss'] = True

        elif etype == 'SUnitDiedEvent':
            tag = event.get('m_unitTagIndex')
            if tag in unit_tags:
                u_info = unit_tags[tag]
                # If it's a hero unit (has a pid), record the death timestamp
                if u_info.get('pid') is not None:
                    pid = u_info['pid']
                    if pid in stats_data:
                        # Fallback: Identify if this is a HERO death for timeline reconstruction
                        # Only proceed if we recognize the hero type and PID is valid (1-10)
                        u_type_clean = clean_text(u_info['type'])
                        player_hero_clean = clean_text(players[pid-1]['hero']) if 0 < pid <= len(players) else None

                        # Heuristic: Match internal name with player hero name
                        u_type_clean_l = u_type_clean.lower()
                        item_to_match = player_hero_clean.lower()
                        
                        # Robust Hero Identification
                        is_summon = any(x in u_type_clean_l for x in ['spiritally', 'egg', 'summon', 'turret', 'decoying', 'pufferfish', 'holohologram', 'camera'])
                        
                        u_internal = u_type_clean_l.replace('hero', '')
                        u_display_mapped = clean_text(get_hero_display_name(u_internal))
                        
                        is_hero = False
                        if u_type_clean_l.startswith('hero') and not is_summon:
                            # 1. Match with mapped display name (e.g. HeroWitchDoctor -> Nazeebo)
                            if u_display_mapped == item_to_match:
                                is_hero = True
                            # 2. Match with internal name fragments (e.g. HeroAbathur -> Abathur)
                            elif item_to_match in u_type_clean_l or u_internal in item_to_match:
                                is_hero = True
                        
                        if is_hero:
                            timestamp = round(gameloop / 16.0, 1)
                            
                            if 'death_timestamps' not in stats_data[pid]:
                                stats_data[pid]['death_timestamps'] = []
                            stats_data[pid]['death_timestamps'].append(timestamp)

                            # Determine Killer
                            killer_pid = event.get('m_killerPlayerId')
                            
                            # If killer PID is invalid (0 or None), try to resolve via unit tag
                            if not killer_pid or killer_pid == 0:
                                k_tag = event.get('m_killerUnitTagIndex')
                                if k_tag and k_tag in unit_tags:
                                    k_info = unit_tags[k_tag]
                                    killer_pid = k_info.get('pid')

                            # Ensure killer_pid is a valid player (1-10)
                            final_killer_pid = killer_pid if (killer_pid and 0 < killer_pid <= len(players)) else None
                            
                            # Create a synthetic PlayerDeath event if not duplicate
                            # (Simple de-dupe: check if we just added one for this gameloop)
                            is_duplicate = False
                            if stats_data['player_deaths']:
                                last_death = stats_data['player_deaths'][-1]
                                if last_death['gameloop'] == gameloop and last_death['victim_pid'] == pid:
                                    is_duplicate = True
                            
                            if not is_duplicate:
                                stats_data['player_deaths'].append({
                                    'timestamp': timestamp,
                                    'victim_pid': pid,
                                    'killer_pid': final_killer_pid,
                                    'gameloop': gameloop,
                                    'source': 'fallback_unit_died'
                                })

        # --- BANS ---
        elif etype == 'SHeroBannedEvent':
            team_id = event.get('m_controllingTeam')
            if team_id is None:
                user_wrapper = event.get('_userid', {})
                if isinstance(user_wrapper, dict):
                    uid = user_wrapper.get('m_userId')
                    if uid is not None and 0 <= uid < len(players):
                        team_id = players[uid]['team']
            
            bans.append({
                'hero': event.get('m_hero', b'').decode('utf-8'),
                'gameloop': gameloop,
                'team': team_id
            })

        # --- TALENTS ---
        elif etype == 'STalentChosenEvent':
            pid = event.get('m_controlPlayerId') or event.get('m_userid')
            if pid and pid in stats_data:
                idx = event.get('m_talentNameIndex')
                player_idx = pid - 1
                if 0 <= player_idx < len(players):
                    hero_n = players[player_idx]['hero']
                    rich_id = get_talent_from_index(hero_n, idx, talents.TALENTS_DB)
                    if rich_id:
                        garbage = ['Vehicle', 'Mount', 'Hearthstone', 'Spray', 'Voice', 'Banner']
                        if any(g in rich_id for g in garbage): continue
                        
                        stats_data[pid]['talents'].append({
                            "timestamp": round(gameloop / 16.0, 1),
                            "talent_name": rich_id,
                            "source": "tracker_legacy"
                        })

        # --- SCORE RESULTS (KDA, Healing, etc.) ---
        elif etype == 'SScoreResultEvent':
            for entry in event.get('m_instanceList', []):
                s_name = entry.get('m_name', b'').decode('utf-8')
                for i, val_list in enumerate(entry.get('m_values', [])):
                    if val_list:
                        pid = i + 1
                        if pid in stats_data:
                            stats_data[pid]['stats'][s_name] = val_list[-1].get('m_value')

        # --- STAT GAME EVENTS (Map Logic & XP) ---
        elif etype == 'SStatGameEvent':
            ename = event.get('m_eventName', b'').decode('utf-8')
            data_map = {d.get('m_key', b'').decode('utf-8'): d.get('m_value') for d in (event.get('m_intData') or []) + (event.get('m_fixedData') or [])}
            str_map = {d.get('m_key', b'').decode('utf-8'): d.get('m_value', b'').decode('utf-8') for d in (event.get('m_stringData') or [])}

            if ename == 'JungleCampCapture':
                team_raw = data_map.get('TeamID', 0)
                team_id = 0 if team_raw == 4096 else 1 if team_raw == 8192 else None
                camp_type = str_map.get('CampType', 'Merc Camp')
                
                is_boss = any(kw in camp_type for kw in ['Boss', 'GraveyardBoss', 'Archangel', 'Webweaver', 'SlimeBoss'])
                event_entry = {
                    'timestamp': round(gameloop / 16.0, 1),
                    'captured_by_team': team_id,
                    'unit_name': camp_type,
                    'gameloop': gameloop
                }
                
                if is_boss: stats_data['boss_captures'].append(event_entry)
                else: stats_data['merc_captures'].append(event_entry)

            elif ename == 'TownStructureDeath':
                destroying_team = None
                k_pid = data_map.get('KillingPlayer')
                if k_pid and 0 < k_pid <= len(players):
                    destroying_team = players[k_pid-1]['team']
                
                stats_data['structure_destructions'].append({
                    'timestamp': round(gameloop / 16.0, 1),
                    'structure_type': str_map.get('UnitType', 'Structure'),
                    'destroyed_by_team': destroying_team,
                    'gameloop': gameloop
                })

            elif ename == 'EndOfGameXPBreakdown':
                pid = data_map.get('PlayerID')
                if pid and pid in stats_data:
                    for k in ['HeroXP', 'MinionXP', 'StructureXP', 'CreepXP', 'SiegeXP', 'TrickleXP']:
                        stats_data[pid]['stats'][k] = round(data_map.get(k, 0) / 4096.0)

            elif ename == 'GameUserLeave':
                # Forensic detection of a player disconnecting
                pid = data_map.get('PlayerID')
                if pid and pid in stats_data:
                    stats_data[pid]['disconnected'] = True
                    stats_data[pid]['dc_gameloop'] = gameloop
                    stats_data[pid]['dc_timestamp'] = round(gameloop / 16.0, 1)

            elif ename == 'PlayerDeath':
                victim_pid = data_map.get('PlayerID')
                killer_pid = data_map.get('KillingPlayer')
                if victim_pid:
                    if 'player_deaths' not in stats_data: stats_data['player_deaths'] = []
                    
                    # De-dupe against fallback
                    existing = next((d for d in stats_data['player_deaths'] if d['gameloop'] == gameloop and d['victim_pid'] == victim_pid), None)
                    
                    if existing:
                        # Update if we have better info (e.g. killer)
                        if killer_pid and not existing['killer_pid']:
                             existing['killer_pid'] = killer_pid if killer_pid and killer_pid > 0 else None
                    else:
                        stats_data['player_deaths'].append({
                            'timestamp': round(gameloop / 16.0, 1),
                            'victim_pid': victim_pid,
                            'killer_pid': killer_pid if killer_pid and killer_pid > 0 else None,
                            'gameloop': gameloop
                        })

    return stats_data, bans


def process_game_events(events, players, stats_data):
    """
    Process game events to extract data not found in tracker events (e.g. talents, hook casts).
    """
    for event in events:
        etype = event['_event']
        if '.' in etype: etype = etype.split('.')[-1]
        gameloop = event['_gameloop']
        
        # --- STITCHES HOOK TRACKING ---
        if etype == 'SCmdEvent':
             raw_uid = event.get('_userid', {}).get('m_userId')
             # m_userId is 0-indexed relative to human slots usually?
             # Actually, in parser.py logic: pid = uid + 1
             if raw_uid is not None:
                 pid = raw_uid + 1
                 if 0 < pid <= len(players):
                     player = players[raw_uid]
                     if 'Stitches' in player['hero']:
                         abil = event.get('m_abil')
                         if abil:
                             link = abil.get('m_abilLink')
                             # Link 579 is confirmed Hook cast
                             if link == 579:
                                 if 'specific_stats' not in stats_data[pid]:
                                     stats_data[pid]['specific_stats'] = {}
                                 
                                 current = stats_data[pid]['specific_stats'].get('HooksThrown', 0)
                                 stats_data[pid]['specific_stats']['HooksThrown'] = current + 1

        elif etype == 'SHeroTalentTreeSelectedEvent':
            uid = event.get('_userid', {}).get('m_userId')
            if uid is not None:
                pid = uid + 1
                if pid in stats_data:
                    idx = event.get('m_index')
                    player_idx = uid
                    if 0 <= player_idx < len(players):
                        hero_n = players[player_idx]['hero']
                        rich_id = get_talent_from_index(hero_n, idx, talents.TALENTS_DB)
                        if rich_id:
                            if not any(t['talent_name'] == rich_id for t in stats_data[pid]['talents']):
                                stats_data[pid]['talents'].append({
                                    "timestamp": round(gameloop / 16.0, 1),
                                    "talent_name": rich_id,
                                    "source": "game_event"
                                })
        
        elif etype == 'SGameUserLeaveEvent':
            uid = event.get('_userid', {}).get('m_userId')
            if uid is not None:
                pid = uid + 1
                if pid in stats_data:
                    # Forensic DC tracking
                    stats_data[pid]['disconnected'] = True
                    stats_data[pid]['dc_gameloop'] = gameloop
                    stats_data[pid]['dc_timestamp'] = round(gameloop / 16.0, 1)

    return stats_data

