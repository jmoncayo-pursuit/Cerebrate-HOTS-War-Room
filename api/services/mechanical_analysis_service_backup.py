
import os
import mpyq
from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest as protocol

class MechanicalAnalysisService:
    @staticmethod
    def analyze_replay(replay_path, hero_name):
        if hero_name.lower() != 'stitches':
            # Currently only Stitches is supported for forensic mechanics
            return None

        try:
            archive = mpyq.MPQArchive(replay_path)
            
            # Use protocol to decode events
            game_events = list(protocol().decode_replay_game_events(archive.read_file('replay.game.events')))
            tracker_events = list(protocol().decode_replay_tracker_events(archive.read_file('replay.tracker.events')))

            # Internal engine name to Display Name mapping
            hero_mapping = {
                'DemonHunter': 'Valla',
                'Amazon': 'Cassia',
                'Barbarian': 'Sonya',
                'WitchDoctor': 'Nazeebo',
                'Wizard': 'Li-Ming',
                'Monk': 'Kharazim',
                'FaerieDragon': 'Brightwing',
                'TraitorLeader': 'Kaelthas',
                'Crusader': 'Johanna',
                'Necromancer': 'Xul',
                'Dryad': 'Lunara',
                'Tinker': 'Gazlowe'
            }

            # Map PIDs to Hero Names
            hero_names_map = {}
            for event in tracker_events:
                if event['_event'] == 'NNet.Replay.Tracker.SUnitBornEvent':
                    unit_type = event.get('m_unitTypeName', b'').decode('utf-8')
                    if unit_type.startswith('Hero'):
                        pid = event.get('m_controlPlayerId')
                        raw_name = unit_type[4:] # Remove 'Hero' prefix
                        hero_names_map[pid] = hero_mapping.get(raw_name, raw_name)

            # Identify the Stitches player dynamically
            details = protocol().decode_replay_details(archive.read_file('replay.details'))
            players_list = details.get('m_playerList', [])
            target_pid = None
            target_uid = None
            
            for i, p in enumerate(players_list):
                name = p.get('m_name', b'').decode('utf-8')
                hero = p.get('m_hero', b'').decode('utf-8')
                # Usually we search for known user names, or fallback to the hero we're analyzing
                if hero == 'Stitches':
                    target_pid = i + 1
                    target_uid = i
                    # If we find 'Discerning' or 'CerebrateUser', it's definitely the user
                    if name in ['Discerning', 'CerebrateUser']:
                        break

            if target_uid is None:
                # Fallback to hardcoded slots if detection fails
                target_uid = 0
                target_pid = 1

            hooks = []
            others = []
            for event in game_events:
                uid = event.get('_userid', {}).get('m_userId')
                if uid == target_uid and event['_event'] == 'NNet.Game.SCmdEvent':
                    abil = event.get('m_abil')
                    if not abil: continue
                    link = abil.get('m_abilLink')
                    ts = round(event['_gameloop'] / 16.0, 1)
                    if link == 575: 
                        hooks.append(ts)
                    else: 
                        others.append({'ts': ts, 'link': link})

            deaths = []
            for event in tracker_events:
                if event['_event'] == 'NNet.Replay.Tracker.SStatGameEvent' and event.get('m_eventName', b'').decode('utf-8') == 'PlayerDeath':
                    data = {d.get('m_key', b'').decode('utf-8'): d.get('m_value') for d in (event.get('m_intData') or []) + (event.get('m_fixedData') or [])}
                    pid = data.get('PlayerID')
                    if pid and pid >= 6: # Enemy team usually 6-10
                        deaths.append({'ts': round(event['_gameloop'] / 16.0, 1), 'hero': hero_names_map.get(pid, f'P{pid}')})

            landed = []
            for h_ts in hooks:
                hit = False
                outcome = []
                victim = None
                # Combo?
                for o in others:
                    if 0 < (o['ts'] - h_ts) <= 1.5:
                        if o['link'] == 574: outcome.append("Slammed (W)")
                        elif o['link'] in [111, 185]: outcome.append("Devoured (E)")
                        hit = True
                        break
                # Lethal?
                for d in deaths:
                    if 0 < (d['ts'] - h_ts) <= 5.0:
                        # Extract victim name from hero_names_map to check team if possible
                        # but we already filtered 'deaths' to be enemies in some versions?
                        # Let's be explicit and re-filter here to be safe.
                        victim_hero = d['hero']
                        # We want to make sure it's an ENEMY death.
                        # The 'deaths' list is already filtered for pid >= 6 in some scripts,
                        # but that's unreliable. Let's filter by team.
                        
                        # Find victim's team
                        is_enemy = True
                        for pid_check, hero_check in hero_names_map.items():
                            if hero_check == victim_hero:
                                # We need player's team. Let's get it from the earlier detection.
                                # Wait, I can just check if victim_hero is 'Stitches' or user hero.
                                if victim_hero == hero_name or victim_hero == 'Stitches':
                                    is_enemy = False
                                break
                        
                        if is_enemy:
                            outcome.append(f"LETHAL: {victim_hero} killed")
                            victim = victim_hero
                            hit = True
                            break
                if hit:
                    landed.append({
                        'time': f"{int(h_ts // 60)}:{int(h_ts % 60):02d}", 
                        'event': f"Hook -> {', '.join(outcome)}",
                        'victim': victim
                    })

            # Quest tracking
            globes = 0
            for event in tracker_events:
                if event['_event'] == 'NNet.Replay.Tracker.SStatGameEvent' and event.get('m_eventName', b'').decode('utf-8') == 'RegenGlobePickedUp':
                    data = {d.get('m_key', b'').decode('utf-8'): d.get('m_value') for d in (event.get('m_intData') or [])}
                    if data.get('PlayerID') == target_pid:
                        globes += 1

            accuracy = round(len(landed)/len(hooks)*100, 1) if hooks else 0
            
            return {
                "hero_deep_dive": "Stitches Hook Analysis",
                "mechanics": [
                    {"label": "Hooks Thrown", "value": len(hooks)},
                    {"label": "Hooks Landed", "value": len(landed)},
                    {"label": "Accuracy", "value": f"{accuracy}%"},
                    {"label": "Lethal Hooks", "value": sum(1 for l in landed if 'LETHAL' in l['event'])}
                ],
                "quest_progression": {
                    "name": "Hungry for More",
                    "stat": "Regen Globes",
                    "value": globes,
                    "bonus": f"+{globes * 30}",
                    "verdict": "RAID BOSS" if globes >= 30 else "SCALING"
                },
                "highlights": landed[:5] # Show top 5 landed hooks
            }
        except Exception as e:
            print(f"Error in MechanicalAnalysis: {e}")
            return None
