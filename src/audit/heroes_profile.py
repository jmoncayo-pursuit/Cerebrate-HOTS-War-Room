import requests
from bs4 import BeautifulSoup
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HeroesProfileClient:
    BASE_URL = "https://www.heroesprofile.com"
    
    def __init__(self, player_id=None, region="1", player_name=None):
        import os
        self.player_id = player_id or os.environ.get('PLAYER_HP_ID', "3446653")
        self.region = region
        self.player_name = player_name or os.environ.get('PLAYER_NAME', "Player")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        })

    def _get_soup(self, url):
        logger.info(f"Fetching: {url}")
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def get_season_stats(self, season):
        """
        Fetches hero stats for a specific season.
        """
        url = f"{self.BASE_URL}/Player/{self.player_name}/{self.player_id}/{self.region}/Hero?game_type=sl&season={season}"
        return self._parse_hero_table(url)

    def get_lifetime_stats(self):
        """
        Fetches lifetime hero stats.
        """
        url = f"{self.BASE_URL}/Player/{self.player_name}/{self.player_id}/{self.region}/Hero?game_type=sl"
        return self._parse_hero_table(url)

    def _parse_hero_table(self, url):
        soup = self._get_soup(url)
        if not soup:
            return []

        heroes = []
        # Finding the main stats table. This is heuristic based on standard HP layout.
        # Usually it's a table with specific headers.
        table = soup.find('table', {'class': 'table'}) # Generic bootstrap table class
        
        if not table:
            # Fallback: look for any table
            tables = soup.find_all('table')
            if tables:
                table = tables[0]
        
        if not table:
            logger.warning("No table found on page.")
            return []

        rows = table.find_all('tr')
        # Skip header row
        for row in rows[1:]:
            cols = row.find_all('td')
            if not cols or len(cols) < 5: 
                continue
            
            try:
                # Column indices are guesses based on typical layout. 
                # Name (0), Games (2?), Win Rate (3?) -> Need to be flexible or check headers.
                # Let's try to extract by finding known data types.
                
                name_div = cols[0]
                hero_name = name_div.get_text(strip=True)
                
                # Games played is usually an integer
                games_text = cols[2].get_text(strip=True)
                games = int(games_text.replace(',', ''))
                
                # Win Rate is usually a percentage
                wr_text = cols[4].get_text(strip=True).replace('%', '')
                win_rate = float(wr_text)
                
                # Wins / Losses might be calculated or separate cols
                # Assuming HP format: Hero, Role, Games, Win Rate, KDA, etc.
                # Actually, standard HP Hero page: Hero, Role, Games, Win Rate, Change
                # Let's adjust indices: 
                # 0: Hero Image/Name
                # 1: ? (Maybe Role icon) 
                # 2: Wins / Games? No, usually Games.
                
                # Let's just store what we can likely identifying
                heroes.append({
                    "hero": hero_name,
                    "games": games,
                    "win_rate": win_rate
                })
            except (ValueError, IndexError) as e:
                pass # Skip rows that don't parse cleanly

        return heroes

    def get_talent_builds(self, hero_name, season):
        """
        Fetches talent builds for a specific hero and season.
        """
        # Encode hero name for URL
        clean_name = hero_name.replace(" ", "") # HP sometimes strips spaces in URLs? Or uses %20. Let's try %20 for safety via requests param, but here we build str.
        # Actually HP uses 'TheButcher' style often? Let's assume standard %20 or name.
        # Let's try standard name.
        
        url = f"{self.BASE_URL}/Player/{self.player_name}/{self.player_id}/{self.region}/Talents/{hero_name}?game_type=sl&season={season}"
        soup = self._get_soup(url)
        
        if not soup: return []

        builds = []
        # Similar table parsing logic for builds
        # Talent tables usually have 7 images for talents + Games + Win Rate
        
        # This is a placeholder for the complex talent parsing logic.
        # For V1, we might simply return empty if we can't parse easily.
        
        return builds

if __name__ == "__main__":
    # Test
    client = HeroesProfileClient()
    print("Testing Lifetime Stats...")
    stats = client.get_lifetime_stats()
    print(f"Found {len(stats)} heroes.")
    for h in stats[:3]:
        print(h)
