import json
import os
import sys
from datetime import datetime

# Add root directory to path to import database_manager
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database_manager import DatabaseManager

# Handle paths relative to script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
MATCH_HISTORY_FILE = os.path.join(PROJECT_ROOT, 'src/data/match_history.json')
PLAYER_PROFILE_FILE = os.path.join(PROJECT_ROOT, 'src/data/player_profile.json')
PLAYER_INTERACTIONS_FILE = os.path.join(PROJECT_ROOT, 'src/data/player_interactions.json')

def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def update_interactions():
    db = DatabaseManager()
    
    # Load from SQL (Get all matches to rebuild interactions)
    # Using a large limit to catch all history
    history = db.get_matches(limit=10000)
    profile = db.get_kv('player_profile') or {}
    
    # Get user's name to determine "with" or "against"
    user_battletag = profile.get('battletag', 'Discerning#11234') # Fallback
    user_name = user_battletag.split('#')[0]
    
    interactions = {}

    print(f"Analyzing {len(history)} matches for player interactions (SQL Source)...")

    for match in history:
        match_id = match.get('id')
        match_date = match.get('timestamp_iso') or match.get('date')
        if match_date == 'Just Now': continue
        
        players = match.get('players', [])
        if not players: continue
        
        # Find user in the match
        user_in_match = next((p for p in players if p.get('name') == user_name or p.get('hero') == match.get('hero')), None)
        if not user_in_match:
            # Fallback: assume the first player who matches the user's hero in history
            user_in_match = next((p for p in players if p.get('hero') == match.get('hero')), None)

        if not user_in_match: continue
        
        user_team = user_in_match.get('team')
        user_won = match.get('result') == 'WIN' or match.get('win') == True
        
        for p in players:
            p_name = p.get('name')
            p_toon = p.get('toon_id')
            
            # Use toon_id as primary key to avoid name collisions (e.g. many people named "Player")
            p_key = p_toon if p_toon else p_name
            
            if not p_name or p_name == user_name: continue
            
            if p_key not in interactions:
                interactions[p_key] = {
                    "id": p_key,
                    "name": p_name,
                    "toon_id": p_toon,
                    "matches": [],
                    "total_with": 0,
                    "total_against": 0,
                    "wins_with": 0,
                    "wins_against": 0
                }
            
            player_record = interactions[p_key]
            is_teammate = p.get('team') == user_team
            
            # Check if match already recorded for this specific player
            if any(m['match_id'] == match_id for m in player_record['matches']):
                continue
                
            match_entry = {
                "match_id": match_id,
                "date": match_date,
                "hero": p.get('hero'),
                "my_hero": user_in_match.get('hero'),
                "team": "WITH" if is_teammate else "AGAINST",
                "result": "WIN" if p.get('win') else "LOSS"
            }
            
            player_record['matches'].append(match_entry)
            
            if is_teammate:
                player_record['total_with'] += 1
                if user_won:
                    player_record['wins_with'] += 1
            else:
                player_record['total_against'] += 1
                if user_won:
                    player_record['wins_against'] += 1

    # Sort matches by date
    for p_name in interactions:
        interactions[p_name]['matches'].sort(key=lambda x: x['date'] or "", reverse=True)
        
    # SAVE TO SQL
    db.set_kv('player_interactions', interactions)
    print(f"Updated {len(interactions)} unique players in SQL.")

    # Legacy Backup
    save_json(PLAYER_INTERACTIONS_FILE, interactions)

if __name__ == "__main__":
    update_interactions()
