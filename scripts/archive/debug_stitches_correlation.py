
import os
import mpyq
from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest as protocol

def debug_stitches_correlation(replay_path):
    archive = mpyq.MPQArchive(replay_path)
    game_events = list(protocol().decode_replay_game_events(archive.read_file('replay.game.events')))
    
    target_uid = 5 # Stitches
    
    hooks = []
    attacks = []
    
    for event in game_events:
        uid = event.get('_userid', {}).get('m_userId')
        if uid == target_uid:
            ts = event['_gameloop']/16.0
            if event['_event'] == 'NNet.Game.SCmdEvent':
                abil = event.get('m_abil')
                if abil and abil.get('m_abilLink') in [181, 185, 186, 575, 579]:
                    hooks.append(ts)
                data = event.get('m_data', {})
                if 'TargetUnit' in data:
                    attacks.append((ts, data['TargetUnit'].get('m_snapshotUnitLink')))

    print("--- Hook-Attack Correlation ---")
    for h_ts in hooks[:20]:
        print(f"Hook thrown at {h_ts:.2f}")
        # Look for attacks within 2s
        matches = [a for a in attacks if h_ts <= a[0] <= h_ts + 2.0]
        if matches:
            for m in matches:
                print(f"  Match? Attack at {m[0]:.2f} on Link {m[1]}")
        else:
            print("  No attack follow-up in 2s")

if __name__ == '__main__':
    path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-02-15 10.12.43 Volskaya Foundry.StormReplay"
    debug_stitches_correlation(path)
