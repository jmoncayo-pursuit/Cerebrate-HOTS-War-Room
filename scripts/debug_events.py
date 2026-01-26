#!/usr/bin/env python3
"""Debug script to see what events are in the replay"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mpyq
from heroprotocol.versions import latest

replay_path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-01-06 22.01.16 Blackheart's Bay.StormReplay"

print("Opening replay...")
archive = mpyq.MPQArchive(replay_path)
protocol = latest()

print("Decoding tracker events...")
tracker_events = protocol.decode_replay_tracker_events(archive.read_file('replay.tracker.events'))

# Find all unique event names
event_names = set()
coin_events = []

for event in tracker_events:
    ename = event['_event']
    event_names.add(ename)
    
    # Look for coin-related events
    if 'doubloon' in ename.lower() or 'coin' in ename.lower() or 'blackheart' in ename.lower():
        coin_events.append(event)

print(f"\nTotal unique event types: {len(event_names)}")
print(f"\nCoin-related events found: {len(coin_events)}")

if coin_events:
    print("\nFirst 5 coin events:")
    for event in coin_events[:5]:
        print(f"  {event['_event']}")
        print(f"    Data: {event}")
        print()

# Search for events with 'Score' in the name (stats are often here)
print("\nScore-related events:")
for ename in sorted(event_names):
    if 'score' in ename.lower() or 'stat' in ename.lower():
        print(f"  - {ename}")
