import os
import sys
import mpyq

# Setup environment
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest
from api.services.replay_parser import parse_replay
from api.services.replay_service import ReplayService

def find_dc_replay():
    replays_dir = '/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts'
    count = 0
    for root, dirs, files in os.walk(replays_dir):
        for f in files:
            if f.endswith('.StormReplay'):
                path = os.path.join(root, f)
                try:
                    archive = mpyq.MPQArchive(path)
                    
                    # 1. Check Tracker Events (GameUserLeave)
                    tracker_events = latest().decode_replay_tracker_events(archive.read_file('replay.tracker.events'))
                    has_dc = False
                    for event in tracker_events:
                        if event.get('_event') == 'SStatGameEvent' and event.get('m_eventName') == b'GameUserLeave':
                            print(f"FOUND GameUserLeave (Tracker) in: {f}")
                            has_dc = True
                            break
                    
                    if not has_dc:
                        # 2. Check Game Events (SGameUserLeaveEvent)
                        game_events = latest().decode_replay_game_events(archive.read_file('replay.game.events'))
                        for event in game_events:
                            etype = event.get('_event')
                            if etype in ['SGameUserLeaveEvent', 'SPlayerLeaveEvent']:
                                print(f"FOUND {etype} (Game) in: {f}")
                                has_dc = True
                                break
                    
                    if has_dc:
                        return path

                except Exception as e:
                    pass
                count += 1
                if count % 25 == 0:
                    print(f"Scanned {count}...")
                if count > 300: # Scan up to 300
                    return None
    return None

if __name__ == "__main__":
    dc_path = find_dc_replay()
    if dc_path:
        print(f"Processing DC match: {dc_path}")
        # Parse and show details
        result = parse_replay(dc_path)
        if result.get('status') == 'success':
            print("\nMATCH DETAILS:")
            print(f"Map: {result['map']}")
            print(f"Hero: {result['hero']}")
            print(f"Result: {result['result']}")
            
            print("\nDISCONNECTED PLAYERS:")
            for p in result['players']:
                if p.get('disconnected'):
                    print(f"- {p['name']} (Team {p['team']})")
            
            # Generate summary (simulated or real call)
            service = ReplayService()
            summary_result = service._generate_match_summary(result)
            if summary_result and summary_result.get('success'):
                print("\nAI FORENSIC SUMMARY:")
                print(f"Verdict: {summary_result['analysis']['verdict']}")
                print(f"Summary: {summary_result['analysis']['summary']}")
                print(f"Key Insight: {summary_result['analysis']['key_insight']}")
            else:
                print("\nFailed to generate summary.")
        else:
            print(f"Failed to parse: {result.get('message')}")
    else:
        print("No DC replay found after scanning.")
