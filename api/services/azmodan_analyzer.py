
import os
import mpyq
from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest as protocol

class AzmodanAnalyzer:
    @staticmethod
    def analyze_replay(replay_path):
        try:
            archive = mpyq.MPQArchive(replay_path)
            game_events = list(protocol().decode_replay_game_events(archive.read_file('replay.game.events')))
            tracker_events = list(protocol().decode_replay_tracker_events(archive.read_file('replay.tracker.events')))
            details = protocol().decode_replay_details(archive.read_file('replay.details'))

            # 1. Identify Azmodan
            azmo_uid = None
            for i, p in enumerate(details['m_playerList']):
                if p.get('m_hero', b'').decode('utf-8') == 'Azmodan':
                    azmo_uid = i
                    break
            
            if azmo_uid is None: return None
            azmo_pid = azmo_uid + 1

            # 2. Track Levels and Deaths
            level_timestamps = {1: 0} # level -> ts
            azmo_deaths_timeline = []
            azmo_kills_timeline = []
            stack_events = [] # (ts, delta)

            hero_names = {i+1: p.get('m_hero', b'').decode('utf-8') for i, p in enumerate(details['m_playerList'])}

            final_hero_dmg = 0
            final_siege_dmg = 0
            final_minion_kills = 0
            annihilation_stacks = 0
            hero_hits_tally = 0

            for e in tracker_events:
                gameloop = e['_gameloop']
                ts = round(gameloop / 16.0, 1)

                if e['_event'] == 'NNet.Replay.Tracker.SStatGameEvent':
                    event_name = e.get('m_eventName', b'').decode('utf-8')
                    data = {d.get('m_key', b'').decode('utf-8'): d.get('m_value') for d in (e.get('m_intData') or []) + (e.get('m_fixedData') or [])}
                    
                    if event_name == 'LevelUp' and data.get('PlayerID') == azmo_pid:
                        level = data.get('Level')
                        level_timestamps[level] = ts
                    elif event_name == 'PlayerDeath':
                        pid = data.get('PlayerID')
                        killer = data.get('KillingPlayer')
                        if killer == azmo_pid:
                            azmo_kills_timeline.append({'ts': ts, 'victim_pid': pid})
                            stack_events.append((ts, 2))
                        if pid == azmo_pid:
                            azmo_deaths_timeline.append({'ts': ts, 'killer_pid': killer})

                elif e['_event'] == 'NNet.Replay.Tracker.SScoreResultEvent':
                    for instance in e.get('m_instanceList', []):
                        name = instance.get('m_name', b'').decode('utf-8')
                        val_list = instance.get('m_values', [])
                        if len(val_list) >= azmo_pid:
                            p_vals = val_list[azmo_pid-1]
                            if not p_vals: continue
                            val = p_vals[-1].get('m_value', 0)

                            if name == 'HeroDamage': final_hero_dmg = val
                            elif name == 'MinionKills': final_minion_kills = val
                            elif 'Annihilation' in name: annihilation_stacks = max(annihilation_stacks, val)
                            elif 'GlobeHeroHits' in name: hero_hits_tally = max(hero_hits_tally, val)

                elif e['_event'] == 'NNet.Replay.Tracker.SUnitDiedEvent':
                    if e.get('m_killerPlayerId') == azmo_pid:
                        # Simple heuristic: most units Azmo kills are minions giving stacks
                        stack_events.append((ts, 2))

            # 3. Track Q Casts
            q_casts = []
            for e in game_events:
                if e['_event'] == 'NNet.Game.SCmdEvent' and e.get('_userid', {}).get('m_userId') == azmo_uid:
                    abil = e.get('m_abil')
                    if abil and abil.get('m_abilLink') in [247, 248, 249]:
                        q_casts.append({'ts': round(e['_gameloop'] / 16.0, 1)})

            final_hero_hits = hero_hits_tally if hero_hits_tally > 0 else max(int(final_hero_dmg / 1200), int(len(q_casts) * 0.4))
            final_stacks = annihilation_stacks if annihilation_stacks > 0 else min(400, final_minion_kills * 2 + final_hero_hits * 2)

            # 4. Synthesize Milestone Timeline
            hits_to_distribute = final_hero_hits
            if q_casts:
                step = max(1, len(q_casts) // max(1, hits_to_distribute))
                for i, q in enumerate(q_casts):
                    if i % step == 0 and hits_to_distribute > 0:
                        stack_events.append((q['ts'], 1))
                        hits_to_distribute -= 1

            stack_events.sort()
            
            cumulative_stacks = 0
            milestones = []
            targets = [75, 150, 225, 300, 400]
            next_target_idx = 0
            
            for ts, delta in stack_events:
                cumulative_stacks += delta
                while next_target_idx < len(targets) and cumulative_stacks >= targets[next_target_idx]:
                    target = targets[next_target_idx]
                    current_level = 1
                    for lv, l_ts in sorted(level_timestamps.items()):
                        if l_ts <= ts: current_level = lv
                        else: break
                    
                    milestones.append({
                        "stacks": target,
                        "time": f"{int(ts // 60)}:{int(ts % 60):02d}",
                        "level": current_level
                    })
                    next_target_idx += 1

            efficiency = round((final_stacks / 400) * 100) if final_stacks < 400 else 100
            
            verdict = "SCALING"
            if final_stacks >= 400: verdict = "APOCALYPTIC"
            elif final_stacks >= 300: verdict = "DREAD LORD"
            elif final_stacks >= 200: verdict = "ARTILLERY"

            return {
                "hero_deep_dive": "Annihilation Forensics",
                "custom_view": "AZMODAN",
                "mechanics": [
                    {"label": "Orbital Strikes", "value": len(q_casts)},
                    {"label": "Heroes Struck (Tally)", "value": final_hero_hits, "details": f"{round(final_hero_hits/len(q_casts)*100 if q_casts else 0)}% Accuracy"},
                    {"label": "Orbital Efficiency", "value": f"{round(final_hero_dmg / max(1, len(q_casts))) if q_casts else 0} Dmg/Shot"}
                ],
                "quest_progression": {
                    "name": "Annihilation",
                    "stat": "Stacks",
                    "value": final_stacks,
                    "bonus": f"+{final_stacks}",
                    "bonus_label": "Bonus Skill Damage",
                    "verdict": verdict,
                    "milestones": milestones
                },
                "tactical_highlights": sorted([
                    {
                        "time": f"{int(k['ts'] // 60)}:{int(k['ts'] % 60):02d}",
                        "event": "Globe Lethal Impact",
                        "type": "KILL",
                        "lethal": True,
                        "victim": hero_names.get(k['victim_pid'], f"Enemy P{k['victim_pid']}")
                    } for k in azmo_kills_timeline
                ], key=lambda x: x['time']),
                "death_highlights": [
                    {
                        "time": f"{int(d['ts'] // 60)}:{int(d['ts'] % 60):02d}",
                        "killer": hero_names.get(d['killer_pid'], "Unknown")
                    } for d in azmo_deaths_timeline
                ]
            }
        except Exception as e:
            return None
