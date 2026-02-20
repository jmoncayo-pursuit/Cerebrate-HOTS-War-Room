
import os
import mpyq
import math
from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest as protocol

class KharazimAnalyzer:
    @staticmethod
    def analyze_replay(replay_path):
        try:
            archive = mpyq.MPQArchive(replay_path)
            game_events = list(protocol().decode_replay_game_events(archive.read_file('replay.game.events')))
            tracker_events = list(protocol().decode_replay_tracker_events(archive.read_file('replay.tracker.events')))
            details = protocol().decode_replay_details(archive.read_file('replay.details'))

            # 1. Identify Kharazim
            target_uid = None
            for i, p in enumerate(details['m_playerList']):
                if p.get('m_hero', b'').decode('utf-8') == 'Monk': # Kharazim internal name
                    target_uid = i
                    break
            
            if target_uid is None: return None
            target_pid = target_uid + 1

            # 2. Track Abilities
            q_casts = 0
            w_casts = 0
            e_casts = 0
            palm_casts = []
            sss_casts = 0
            
            for e in game_events:
                if e['_event'] == 'NNet.Game.SCmdEvent' and e.get('_userid', {}).get('m_userId') == target_uid:
                    abil = e.get('m_abil')
                    if abil:
                        link = abil.get('m_abilLink')
                        ts = round(e['_gameloop'] / 16.0, 1)
                        if link == 484: q_casts += 1
                        elif link == 489: w_casts += 1
                        elif link == 488: e_casts += 1
                        elif link == 483: # Divine Palm
                            palm_casts.append({'ts': ts, 'gameloop': e['_gameloop']})
                        elif link == 487: sss_casts += 1

            # 3. Analyze Deaths for Palm Saves
            deaths = []
            for e in tracker_events:
                if e['_event'] == 'NNet.Replay.Tracker.SStatGameEvent' and e.get('m_eventName', b'').decode('utf-8') == 'PlayerDeath':
                    data = {d.get('m_key', b'').decode('utf-8'): d.get('m_value') for d in (e.get('m_intData') or [])}
                    pid = data.get('PlayerID')
                    if pid:
                        deaths.append({'ts': round(e['_gameloop'] / 16.0, 1), 'pid': pid})

            palm_saves = 0
            highlights = []
            for palm in palm_casts:
                h_ts = palm['ts']
                # A Palm "Save" is if the target DID NOT die in the next 3 seconds
                # (Simple heuristic, as we can't easily see who was targeted without more complex mapping, 
                # but we can look for "Combat Action" in similar timeframe)
                saved = True
                for d in deaths:
                    if 0 <= (d['ts'] - h_ts) <= 3.0:
                        # Someone died right after Palm... likely the target or near them
                        # If a teammate died, it wasn't a save.
                        # Note: This is an approximation.
                        saved = False
                        break
                
                if saved:
                    palm_saves += 1
                    highlights.append({
                        "time": f"{int(h_ts // 60)}:{int(h_ts % 60):02d}",
                        "event": "Divine Palm Save",
                        "type": "SAVE",
                        "lethal": False
                    })

            # Score Results for Context
            healing = 0
            damage = 0
            for e in tracker_events:
                if e['_event'] == 'NNet.Replay.Tracker.SScoreResultEvent':
                    for instance in e.get('m_instanceList', []):
                        name = instance.get('m_name', b'').decode('utf-8')
                        val_list = instance.get('m_values', [])
                        if len(val_list) >= target_pid:
                            val = val_list[target_pid-1][-1].get('m_value', 0)
                            if name == 'Healing': healing = val
                            elif name == 'HeroDamage': damage = val

            verdict = "TACTICAL ANCHOR"
            if palm_saves >= 5: verdict = "DIVINE PROTECTOR"
            elif damage > 50000: verdict = "BATTLE MONK"

            # Estimate Insight uptime based on Dash frequency (Radiant Dash is primary proc consumer)
            # Standard Insight monk dashes ~3-4 times per minute in combat.
            game_length_min = len(game_events) / (16.0 * 60.0)
            dashes_per_min = q_casts / game_length_min if game_length_min > 0 else 0
            uptime = min(100, round(dashes_per_min * 25)) # Heuristic: 4 dashes/min = 100% uptime

            return {
                "hero_deep_dive": "Monastic Combat Audit",
                "custom_view": "KHARAZIM",
                "mechanics": [
                    {"label": "Palm Saves", "value": palm_saves},
                    {"label": "Palm Casts", "value": len(palm_casts)},
                    {"label": "Insight Uptime", "value": f"{uptime}%", "details": f"{q_casts} Dashes"},
                    {"label": "Combat Throughput", "value": f"{round(damage/1000)}k / {round(healing/1000)}k"}
                ],
                "quest_progression": {
                    "name": "Insight",
                    "stat": "Cool-off Reduction",
                    "value": q_casts,
                    "bonus": f"{q_casts} Procs",
                    "bonus_label": "Dash Resets",
                    "verdict": verdict
                },
                "tactical_highlights": sorted(highlights, key=lambda x: x['time'])
            }
        except Exception as e:
            return None
