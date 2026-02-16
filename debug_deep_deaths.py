import json; sys.modules['imp'] = setup_imp_shim(); import types; import mpyq; from heroprotocol.versions import latest; from api.services.replay_parser.tracker import process_tracker_events; archive = mpyq.MPQArchive('/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-01-21 00.52.33 Dragon Shire.StormReplay'); protocol = latest(); events = protocol.decode_replay_tracker_events(archive.read_file('replay.tracker.events'));

# Manual inspection of specific death events
for e in events:
    if e['_event'] == 'NNet.Replay.Tracker.SUnitDiedEvent':
        if e.get('m_killerPlayerId') == 0 or e.get('m_killerPlayerId') is None:
             print(f"Death at {e['_gameloop']}: KillerPID={e.get('m_killerPlayerId')} Tag={e.get('m_unitTagIndex')} KillerTag={e.get('m_killerUnitTagIndex')}")
