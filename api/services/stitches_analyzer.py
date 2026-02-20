
import os
import mpyq
from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest as protocol
import math

class PositionTracker:
    def __init__(self):
        self.unit_positions = {} # unit_tag_index -> list of (gameloop, x, y)
        self.tag_to_hero = {} # unit_tag_index -> hero_name
        self.index_to_tag = {} # unit_tag_index -> full_tag

    def add_born(self, event):
        tag_index = event['m_unitTagIndex']
        tag_recycle = event['m_unitTagRecycle']
        full_tag = (tag_index << 18) | tag_recycle
        hero_name = event['m_unitTypeName'].decode('utf-8')
        
        self.tag_to_hero[tag_index] = hero_name
        self.index_to_tag[tag_index] = full_tag
        self._add_pos(tag_index, event['_gameloop'], event['m_x'], event['m_y'])

    def add_positions(self, event):
        loop = event['_gameloop']
        unit_index = event['m_firstUnitIndex']
        for i in range(0, len(event['m_items']), 3):
            unit_index += event['m_items'][i]
            x = event['m_items'][i+1]
            y = event['m_items'][i+2]
            self._add_pos(unit_index, loop, x, y)

    def _add_pos(self, index, loop, x, y):
        if index not in self.unit_positions:
            self.unit_positions[index] = []
        self.unit_positions[index].append((loop, x, y))

    def get_pos(self, tag_index, loop):
        if tag_index not in self.unit_positions:
            return None
        
        # Find closest loop <= targeted loop
        best_pos = None
        for l, x, y in self.unit_positions[tag_index]:
            if l <= loop:
                best_pos = (x, y)
            else:
                break
        return best_pos

class StitchesAnalyzer:
    @staticmethod
    def analyze_replay(replay_path):
        try:
            archive = mpyq.MPQArchive(replay_path)
            
            # Decode events
            game_events = list(protocol().decode_replay_game_events(archive.read_file('replay.game.events')))
            details = protocol().decode_replay_details(archive.read_file('replay.details'))
            tracker_events = list(protocol().decode_replay_tracker_events(archive.read_file('replay.tracker.events')))

            # --- IDENTIFY PLAYERS & HEROES ---
            uid_hero_map = {}
            target_uid = None
            uid_team_map = {}

            for i, p in enumerate(details['m_playerList']):
                name = p.get('m_name', b'').decode('utf-8')
                hero = p.get('m_hero', b'').decode('utf-8')
                team = p.get('m_teamId')
                uid_hero_map[i] = {'name': name, 'hero': hero, 'team': team}
                uid_team_map[i] = team
                
                if hero == 'Stitches':
                    if name in ['Discerning', 'CerebrateUser'] or target_uid is None:
                        target_uid = i

            if target_uid is None: return None
            
            target_pid = target_uid + 1
            stitches_team = uid_team_map[target_uid]

            # --- BUILD UNIT LINK MAP ---
            link_counts = {}
            for event in game_events:
                if event['_event'] == 'NNet.Game.SSelectionDeltaEvent':
                    uid = event['_userid']['m_userId']
                    delta = event.get('m_delta', {})
                    subgroups = delta.get('m_addSubgroups', [])
                    if subgroups:
                        link = subgroups[0]['m_unitLink']
                        if uid not in link_counts: link_counts[uid] = {}
                        link_counts[uid][link] = link_counts[uid].get(link, 0) + 1

            link_to_hero = {}
            for uid, counts in link_counts.items():
                if uid in uid_hero_map:
                    best_link = max(counts.items(), key=lambda x: x[1])[0]
                    link_to_hero[best_link] = uid_hero_map[uid]

            # --- DETECT HOOKS ---
            hooks = []
            attack_cmds = []
            last_hook_loop = -1000
            for event in game_events:
                uid = event.get('_userid', {}).get('m_userId')
                gameloop = event['_gameloop']
                ts = round(gameloop / 16.0, 1)

                if uid == target_uid:
                    if event['_event'] == 'NNet.Game.SCmdEvent':
                        abil = event.get('m_abil')
                        data = event.get('m_data', {})
                        if abil:
                            link = abil.get('m_abilLink')
                            # Hook IDs vary by patch: 185, 186 (Classic/Tomb), 575, 579 (Modern)
                            if link in [181, 185, 186, 575, 579, 580]:
                                if 'TargetPoint' in data or 'TargetUnit' in data:
                                    if gameloop - last_hook_loop > 20: # Cooldown is ~16s, but allowing for rapid misfire/reset logic
                                        hooks.append({'ts': ts, 'gameloop': gameloop})
                                        last_hook_loop = gameloop
                        
                        if data and 'TargetUnit' in data:
                            target_link = data['TargetUnit'].get('m_snapshotUnitLink')
                            if target_link:
                                attack_cmds.append({'ts': ts, 'link': target_link})

            # --- VALIDATE HITS & DEATHS ---
            deaths = []
            stitches_kills = 0
            pos_tracker = PositionTracker()
            pid_to_tag_index = {}

            for event in tracker_events:
                e_type = event['_event']
                if e_type == 'NNet.Replay.Tracker.SUnitBornEvent':
                    pos_tracker.add_born(event)
                    hero_name = event['m_unitTypeName'].decode('utf-8')
                    tag_index = event['m_unitTagIndex']
                    pid = event['m_controlPlayerId']
                    if 1 <= pid <= 10 and 'Hero' in hero_name:
                         if pid not in pid_to_tag_index or 'Pilot' not in hero_name: # Prefer Mech/Main Hero
                             pid_to_tag_index[pid] = tag_index
                elif e_type == 'NNet.Replay.Tracker.SUnitPositionsEvent':
                    pos_tracker.add_positions(event)
                elif e_type == 'NNet.Replay.Tracker.SStatGameEvent' and event.get('m_eventName', b'').decode('utf-8') == 'PlayerDeath':
                     data = {d.get('m_key', b'').decode('utf-8'): d.get('m_value') for d in (event.get('m_intData') or []) + (event.get('m_fixedData') or [])}
                     pid = data.get('PlayerID')
                     killer = data.get('KillingPlayer')
                     if pid: deaths.append({'ts': round(event['_gameloop'] / 16.0, 1), 'pid': pid, 'killer': killer})
                     if killer == target_pid: stitches_kills += 1

            landed_hooks = []
            displacement_sum = 0
            max_displacement = 0
            stitches_tag_index = pid_to_tag_index.get(target_pid)

            for hook in hooks:
                h_ts = hook['ts']
                h_loop = hook['gameloop']
                hit_confirmed = False
                victim_info = None
                window_start, window_end = h_ts, h_ts + 1.5

                for cmd in attack_cmds:
                    if (h_ts - 0.1) <= cmd['ts'] <= (h_ts + 2.0):
                        possible_victim = link_to_hero.get(cmd['link'])
                        if possible_victim and possible_victim['team'] != stitches_team and possible_victim['hero'] != 'Stitches':
                            victim_info = possible_victim
                            hit_confirmed = True
                            break 
                
                # Heuristic 2: Immediate Death Confirmation (for lethal snipes where no attack cmd follows)
                if not hit_confirmed:
                    for d in deaths:
                        if 0 <= (d['ts'] - h_ts) <= 1.5:
                            v_pid = d['pid']
                            # uid_hero_map is 0-indexed, PIDs are 1-indexed
                            v_info = uid_hero_map.get(v_pid - 1)
                            if v_info and v_info['team'] != stitches_team and v_info['hero'] != 'Stitches':
                                 victim_info = v_info
                                 hit_confirmed = True
                                 break
                
                if hit_confirmed and victim_info:
                    displacement = 0
                    victim_pid = next((u_idx + 1 for u_idx, info in uid_hero_map.items() if info['hero'] == victim_info['hero'] and info['team'] == victim_info['team']), None)
                    
                    if stitches_tag_index and victim_pid:
                        v_tag_index = pid_to_tag_index.get(victim_pid)
                        
                        s_pos = pos_tracker.get_pos(stitches_tag_index, h_loop)
                        v_pos = pos_tracker.get_pos(v_tag_index, h_loop) if v_tag_index else None
                        
                        if s_pos and v_pos:
                            displacement = math.sqrt((s_pos[0] - v_pos[0])**2 + (s_pos[1] - v_pos[1])**2)
                            displacement_sum += displacement
                            max_displacement = max(max_displacement, displacement)

                    is_lethal = False
                    if victim_pid:
                        for d in deaths:
                            if d['pid'] == victim_pid and 0 < (d['ts'] - h_ts) <= 5.0:
                                is_lethal = True
                                break
                    landed_hooks.append({
                        'time': f"{int(h_ts // 60)}:{int(h_ts % 60):02d}", 
                        'event': f"Hooked {victim_info['hero']}" + (" (LETHAL)" if is_lethal else ""), 
                        'victim': victim_info['hero'], 
                        'lethal': is_lethal,
                        'displacement': round(displacement, 1)
                    })

            # --- SOCIAL ---
            focus_counts = {}
            for cmd in attack_cmds:
                v_info = link_to_hero.get(cmd['link'])
                if v_info and v_info['team'] != stitches_team:
                     name = v_info['hero']
                     focus_counts[name] = focus_counts.get(name, 0) + 1
            top_focus = sorted(focus_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # --- TACTICAL TIMELINE ---
            tactical_events = []
            for lh in landed_hooks:
                h_min, h_sec = map(int, lh['time'].split(':'))
                tactical_events.append({
                    'time': lh['time'], 
                    'time_raw': h_min*60+h_sec, 
                    'event': lh['event'], 
                    'type': 'HOOK', 
                    'victim': lh['victim'], 
                    'lethal': lh['lethal'],
                    'displacement': lh['displacement']
                })
            
            for d in deaths:
                if d['killer'] == target_pid:
                    is_hook_kill = any(lh['victim'] == uid_hero_map[d['pid']-1]['hero'] and 0 <= (d['ts'] - (int(lh['time'].split(':')[0])*60 + int(lh['time'].split(':')[1]))) <= 5.0 for lh in landed_hooks)
                    if not is_hook_kill:
                        v_name = uid_hero_map[d['pid']-1]['hero']
                        tactical_events.append({'time': f"{int(d['ts'] // 60)}:{int(d['ts'] % 60):02d}", 'time_raw': d['ts'], 'event': f"Direct Kill: {v_name}", 'type': 'KILL', 'victim': v_name, 'lethal': True})

            death_events = []
            for d in deaths:
                if d['pid'] == target_pid:
                    killer_idx = d['killer'] - 1 if d['killer'] else -1
                    k_name = uid_hero_map[killer_idx]['hero'] if (killer_idx >= 0 and killer_idx in uid_hero_map) else "Minions / Towers / Mercs"
                    death_events.append({'time': f"{int(d['ts'] // 60)}:{int(d['ts'] % 60):02d}", 'time_raw': d['ts'], 'event': f"YOU WERE KILLED BY {k_name}", 'type': 'DEATH', 'victim': 'Stitches', 'killer': k_name, 'lethal': True})

            tactical_events.sort(key=lambda x: x['time_raw'])
            death_events.sort(key=lambda x: x['time_raw'])
            accuracy = round(len(landed_hooks)/len(hooks)*100, 1) if hooks else 0
            
            globes = 0
            for event in tracker_events:
                if event['_event'] == 'NNet.Replay.Tracker.SStatGameEvent' and event.get('m_eventName', b'').decode('utf-8') == 'RegenGlobePickedUp':
                    data = {d.get('m_key', b'').decode('utf-8'): d.get('m_value') for d in (event.get('m_intData') or [])}
                    if data.get('PlayerID') == target_uid + 1: globes += 1

            lethality_count = sum(1 for l in landed_hooks if l['lethal'])
            lethality_rate = round(lethality_count / len(landed_hooks) * 100, 1) if landed_hooks else 0
            avg_displacement = round(displacement_sum / len(landed_hooks), 1) if landed_hooks else 0

            return {
                "hero_deep_dive": "Stitches Hook Analysis",
                "mechanics": [
                    {"label": "Hooks Thrown", "value": len(hooks)}, 
                    {"label": "Hooks Landed", "value": len(landed_hooks)}, 
                    {"label": "Accuracy", "value": f"{accuracy}%"}, 
                    {"label": "Lethal Hooks", "value": lethality_count},
                    {"label": "Lethality Rate", "value": f"{lethality_rate}%"},
                    {"label": "Avg Displacement", "value": f"{avg_displacement} units"},
                    {"label": "Max Displacement", "value": f"{round(max_displacement, 1)} units"}
                ],
                "social_mechanics": {"focus_distribution": {k: v for k, v in top_focus}, "most_targeted_enemy": top_focus[0][0] if top_focus else "None"},
                "quest_progression": {"name": "Hungry for More", "stat": "Regen Globes", "value": globes, "bonus": f"+{globes * 30}", "bonus_label": "Total HP Gained", "verdict": "RAID BOSS" if globes >= 30 else "SCALING"},
                "highlights": tactical_events,
                "tactical_highlights": tactical_events,
                "death_highlights": death_events
            }
        except Exception as e:
            return None
