
import json
from api.services.database import DatabaseManager

def calculate_winrate(hero_name, map_name):
    db = DatabaseManager()
    
    # We need to query manually to filter by "My" player logic if possible, 
    # but the prompt asks for "Kharazim's winrate". 
    # Usually this implies the user's winrate with that hero on that map.
    # However, since I don't know the exact user ID, I will check 
    # matches where Kharazim was played and the replay file implies it's the uploaded user (usually the one with 'local' flag or just all rows if we want general stats, but usually this is a personal war room).
    #
    # Wait, the `get_matches` allows filtering by hero and map.
    # But `get_matches` returns the match details. 
    # We need to check if the specific player (Kharazim) won.
    
    matches = db.get_matches(limit=1000, hero=hero_name, map_name=map_name, include_players=True)
    
    total_games = 0
    wins = 0
    
    for m in matches:
        players = m.get('players', [])
        # Find the Kharazim player in this match
        # Assuming the user is interested in THEIR winrate, or global?
        # Given "My garden of terror carry", the context is personal.
        # But "whats kharazims winrate" could be general.
        # Let's calculate stats for the specific hero in those matches.
        
        # ACTUALLY: The `get_matches` with `hero=` filter joins on match_players.
        # But it returns the *match*. 
        # We need to see if the match result for that hero was a win.
        # Since `match_players` doesn't strictly store "win" boolean in the JOIN result of `get_matches` (which selects m.*),
        # we have to look at the players list or the match result.
        
        # If the user filtered by hero=Kharazim, `get_matches` returns matches where Kharazim was present.
        # We need to find which team Kharazim was on, and if that team won.
        
        # Filter for the specific hero in the player list
        kharazim_players = [p for p in players if p['hero'] == hero_name]
        
        for p in kharazim_players:
            total_games += 1
            if p['win']:
                wins += 1
                
    if total_games == 0:
        print(f"No games found for {hero_name} on {map_name}.")
    else:
        wr = (wins / total_games) * 100
        print(f"Win Rate for {hero_name} on {map_name}: {wr:.1f}% ({wins}/{total_games} games)")

if __name__ == "__main__":
    calculate_winrate("Kharazim", "Garden of Terror")
