#!/usr/bin/env python3
"""
Find ALL event names in a Blackheart's Bay replay
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mpyq
from heroprotocol.versions import latest

# Monkey-patch imp for Python 3.13
import importlib.util
import sys

class FakeImp:
    PY_SOURCE = 1
    PKG_DIRECTORY = 5
    
    @staticmethod
    def find_module(name, path=None):
        try:
            spec = importlib.util.find_spec(name, path)
            if spec:
                return (None, spec.origin, ('', '', FakeImp.PY_SOURCE))
        except:
            pass
        return None
    
    @staticmethod
    def load_source(name, pathname):
        spec = importlib.util.spec_from_file_location(name, pathname)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            return module
        return None

sys.modules['imp'] = FakeImp()

replay_path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-01-06 22.01.16 Blackheart's Bay.StormReplay"

print("Opening replay...")
archive = mpyq.MPQArchive(replay_path)
protocol = latest()

print("Decoding tracker events...")
tracker_events = protocol.decode_replay_tracker_events(archive.read_file('replay.tracker.events'))

# Find all SStatGameEvent event names
stat_events = set()
for event in tracker_events:
    if 'SStatGameEvent' in event['_event']:
        ename = event.get('m_eventName', b'').decode('utf-8') if isinstance(event.get('m_eventName'), bytes) else str(event.get('m_eventName', ''))
        if ename:
            stat_events.add(ename)

print(f"\nFound {len(stat_events)} unique SStatGameEvent types:")
for ename in sorted(stat_events):
    print(f"  - {ename}")

# Check specifically for coin events
coin_related = [e for e in stat_events if 'doubloon' in e.lower() or 'coin' in e.lower() or 'blackheart' in e.lower()]
print(f"\nCoin-related events: {len(coin_related)}")
for e in coin_related:
    print(f"  - {e}")
