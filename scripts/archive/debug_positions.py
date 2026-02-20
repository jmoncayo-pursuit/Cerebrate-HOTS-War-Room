
import os
import mpyq
from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest as protocol
import math

def debug_stitches_pos(replay_path):
    archive = mpyq.MPQArchive(replay_path)
    
    # 1. Map Unit Tags to Heroes
    # We only need tracker events for this
    tracker_events = list(protocol().decode_replay_tracker_events(archive.read_file('replay.tracker.events')))
    
    unit_to_hero = {}
    for event in tracker_events:
        if event['_event'] == 'NNet.Replay.Tracker.SUnitBornEvent':
            tag = (event['m_unitTagIndex'] << 18) | event['m_unitTagRecycle']
            name = event['m_unitTypeName'].decode('utf-8')
            unit_to_hero[tag] = {"name": name, "pid": event['m_controlPlayerId']}
            
    stitches_tag = None
    for tag, info in unit_to_hero.items():
        if 'HeroStitches' in info['name']:
            stitches_tag = tag
            print(f"Stitches Hero tag: {tag} PID: {info['pid']}")
            break
            
    if not stitches_tag:
        print("Stitches not found in UnitBornEvents")
        return

    # 2. Track positions
    positions = []
    for event in tracker_events:
        if event['_event'] == 'NNet.Replay.Tracker.SUnitPositionsEvent':
            unit_index = event['m_firstUnitIndex']
            for i in range(0, len(event['m_items']), 3):
                unit_index += event['m_items'][i]
                x = event['m_items'][i+1]
                y = event['m_items'][i+2]
                
                if unit_index == (stitches_tag >> 18):
                    positions.append({'loop': event['_gameloop'], 'x': x, 'y': y})
    
    print(f"Found {len(positions)} positions for Stitches")
    if positions:
         print(f"Sample: {positions[100] if len(positions) > 100 else positions[0]}")

if __name__ == "__main__":
    path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-02-15 10.12.43 Volskaya Foundry.StormReplay"
    debug_stitches_pos(path)
