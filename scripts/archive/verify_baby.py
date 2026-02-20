import os
import json
import sqlite3
from api.services.replay_service import ReplayService
from api.services.database.manager import DatabaseManager
from dotenv import load_dotenv

# Initialize
load_dotenv()
replay_service = ReplayService()

# Re-audit the Raynor match
match_id = "a711f49caa15b7c3"
print(f"--- Re-testing Educated Baby for {match_id} ---")

# Pull raw data as it would come from parser
db = DatabaseManager()
with db._get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM matches WHERE id = ?", (match_id,))
    match_row = cursor.fetchone()
    
    cursor.execute("SELECT * FROM match_players WHERE match_id = ?", (match_id,))
    player_rows = cursor.fetchall()

if match_row:
    m_map = match_row['map']
    hero = match_row['hero']
    raw_stats = json.loads(match_row['raw_stats'])
    
    players = []
    for p_row in player_rows:
        p = dict(p_row)
        p['stats'] = json.loads(p['stats']) if p['stats'] else {}
        p['talents'] = json.loads(p['talents']) if p['talents'] else []
        p['name'] = p['player_name']
        players.append(p)
    
    match_data = {
        'id': match_id,
        'map': m_map,
        'hero': hero,
        'result': match_row['result'],
        'duration': match_row['duration'],
        'players': players,
        'raw_stats': raw_stats
    }
    
    # Generate new analysis
    analysis = replay_service._generate_match_summary(match_data)
    
    print("\n--- NEW AI OUTPUT ---")
    print(json.dumps(analysis, indent=2))
else:
    print("Match not found.")
