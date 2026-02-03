import os
import sys
import mpyq
import json
import sqlite3

# Setup environment
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest
from api.logger import ColoredLogger
from api.services.database import DatabaseManager

def migrate_historical_dcs():
    db = DatabaseManager()
    replays_dir = '/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts'
    
    ColoredLogger.signal("MIGRATION", f"Starting historical DC reconciliation in {replays_dir}")
    
    scanned = 0
    fixed_matches = 0
    total_leavers_found = 0
    
    # 1. Get all match IDs that need checking (or just scan all local files)
    # Mapping filename/match_id is expensive, so we scan and match by filename logic or match_id
    
    for root, dirs, files in os.walk(replays_dir):
        for f in files:
            if f.endswith('.StormReplay'):
                path = os.path.join(root, f)
                scanned += 1
                
                try:
                    archive = mpyq.MPQArchive(path)
                    protocol = latest()
                    
                    # We need the match_id to update the DB
                    from api.services.replay_parser.header import get_match_id
                    mid = get_match_id(path)
                    
                    # Faster check: Does this match even exist in our DB?
                    with db._get_connection() as conn:
                        exists = conn.execute("SELECT id FROM matches WHERE id = ?", (mid,)).fetchone()
                        if not exists:
                            continue

                    # Forensic check for DCs
                    has_dc = False
                    dc_players = [] # list of (user_id, ts)
                    
                    # Check Game Events
                    game_events = protocol.decode_replay_game_events(archive.read_file('replay.game.events'))
                    
                    # Need game length for filtering
                    header = protocol.decode_replay_header(archive.header['user_data_header']['content'])
                    game_len = header.get('m_elapsedGameLoops', 0) / 16.0
                    
                    for event in game_events:
                        if event.get('_event') == 'NNet.Game.SGameUserLeaveEvent':
                            uid = event.get('_userid', {}).get('m_userId')
                            ts = event.get('_gameloop', 0) / 16.0
                            
                            # Filter end-of-game departures
                            if ts < game_len - 20:
                                dc_players.append((uid, ts))
                                has_dc = True
                    
                    if has_dc:
                        # Update Database
                        with db._get_connection() as conn:
                            # 1. Update match_players
                            for uid, ts in dc_players:
                                # uid in game events is 0-indexed, relates to m_playerList order or userId
                                # In our DB, we store player_name, hero, etc. 
                                # We'll try to find the player by their index/userId if possible, 
                                # but usually we link by toon_handle.
                                # Let's fetch the players for this match to map uid -> toon_handle
                                details = protocol.decode_replay_details(archive.read_file('replay.details'))
                                if uid < len(details['m_playerList']):
                                    p_details = details['m_playerList'][uid]
                                    p_name = p_details['m_name'].decode('utf-8')
                                    
                                    # Update the match_players record
                                    conn.execute("""
                                        UPDATE match_players 
                                        SET disconnected = 1, dc_timestamp = ? 
                                        WHERE match_id = ? AND player_name = ?
                                    """, (ts, mid, p_name))
                                    
                                    total_leavers_found += 1
                            
                            conn.commit()
                        
                        # Trigger social stat recalculation for this match
                        db.update_social_stats(mid)
                        fixed_matches += 1
                        
                        time_str = f"{int(dc_players[0][1]//60)}:{int(dc_players[0][1]%60):02d}"
                        ColoredLogger.success(f"Forensic DC fixed: {f} ({dc_players[0][0]} @ {time_str})", "MIGRATION")
                        
                except Exception as e:
                    # ColoredLogger.error(f"Failed to process {f}: {e}", "MIGRATION")
                    pass
                
                if scanned % 50 == 0:
                    ColoredLogger.processing(f"Scanned {scanned} replays...", "MIGRATION")

    ColoredLogger.signal("MIGRATION", f"Reconciliation Complete. {fixed_matches} matches rejuvenated. {total_leavers_found} leaver events recorded.")

if __name__ == "__main__":
    migrate_historical_dcs()
