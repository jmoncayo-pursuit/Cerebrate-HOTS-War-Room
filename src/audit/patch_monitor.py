"""
Obsolete Build Detection: Patch Monitor & Obsolete Build Detector

Automatically detects when your builds become obsolete due to patch changes.

Features:
1. Scrapes patch notes from heroespatchnotes.com
2. Identifies talent nerfs/buffs for your active heroes
3. Flags "obsolete builds" (builds using nerfed talents)
4. Generates alerts before you queue with outdated builds
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re


class PatchMonitor:
    """Monitors HotS patch notes and detects talent changes."""
    
    def __init__(self):
        self.base_url = "https://heroespatchnotes.com"
        self.cache_file = "src/data/patch_cache.json"
        
    def fetch_recent_patches(self, since_date=None):
        """
        Fetch all patches since a given date.
        
        Args:
            since_date (datetime): Only fetch patches after this date
            
        Returns:
            list: List of patch objects with date, version, and changes
        """
        if since_date is None:
            # Default: Last 6 months
            since_date = datetime.now() - timedelta(days=180)
            
        print(f"Fetching patches since {since_date.strftime('%Y-%m-%d')}...")
        
        try:
            # Fetch the main patch notes page
            response = requests.get(f"{self.base_url}/hero", timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all patch entries
            # Note: This is a simplified scraper - actual implementation
            # would need to be tailored to the site's structure
            patches = []
            
            # Placeholder: In real implementation, parse the HTML structure
            # For now, return mock data structure
            patches.append({
                "date": "2025-06-18",
                "version": "2.55",
                "url": f"{self.base_url}/hero/gazlowe",
                "heroes_changed": ["Gazlowe", "Malthael", "Johanna"]
            })
            
            return patches
            
        except requests.RequestException as e:
            print(f"Error fetching patches: {e}")
            return []
    
    def get_hero_changes(self, hero_name, since_date=None):
        """
        Get all changes for a specific hero since a date.
        
        Args:
            hero_name (str): Hero name (e.g., "Gazlowe")
            since_date (datetime): Only fetch changes after this date
            
        Returns:
            list: List of changes with date, talent, and type (buff/nerf)
        """
        if since_date is None:
            since_date = datetime.now() - timedelta(days=180)
            
        hero_slug = hero_name.lower().replace(" ", "").replace(".", "")
        url = f"{self.base_url}/hero/{hero_slug}"
        
        print(f"Fetching changes for {hero_name}...")
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            changes = []
            
            # Parse patch notes (simplified - needs real implementation)
            # Example structure:
            changes.append({
                "date": "2025-06-18",
                "patch": "2.55",
                "talent": "Goblin Fusion",
                "tier": 7,
                "change_type": "nerf",
                "description": "Moved from Level 16 to Level 4, damage bonus reduced from 50% to 25%",
                "severity": "major"  # major, minor, rework
            })
            
            return changes
            
        except requests.RequestException as e:
            print(f"Error fetching hero changes: {e}")
            return []
    
    def save_cache(self, data):
        """Save patch data to cache file."""
        with open(self.cache_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_cache(self):
        """Load patch data from cache file."""
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}



class ObsoleteBuildDetector:
    """Detects when your builds use nerfed talents (obsolete builds)."""
    
    def __init__(self, patch_monitor):
        self.patch_monitor = patch_monitor
        
    def analyze_build(self, hero_name, build_talents, season_start_date):
        """
        Analyze if a build has become obsolete due to patch changes.
        
        Args:
            hero_name (str): Hero name
            build_talents (dict): Talent choices by tier {1: "Talent Name", 4: "...", ...}
            season_start_date (datetime): When you started using this build
            
        Returns:
            dict: Analysis with obsolete status and affected talents
        """
        # Get all changes since season start
        changes = self.patch_monitor.get_hero_changes(hero_name, season_start_date)
        
        affected_talents = []
        obsolete_score = 0
        
        for change in changes:
            talent_name = change['talent']
            
            # Check if this build uses the changed talent
            if talent_name in build_talents.values():
                affected_talents.append({
                    "talent": talent_name,
                    "tier": change['tier'],
                    "change_type": change['change_type'],
                    "description": change['description'],
                    "severity": change['severity'],
                    "patch_date": change['date']
                })
                
                # Calculate obsolete score
                if change['change_type'] == 'nerf':
                    if change['severity'] == 'major':
                        obsolete_score += 10
                    elif change['severity'] == 'minor':
                        obsolete_score += 3
                elif change['change_type'] == 'buff':
                    obsolete_score -= 5  # Build got better
        
        # Determine status
        if obsolete_score >= 10:
            status = "OBSOLETE"  # Build is obsolete
            recommendation = "ABANDON - Major nerfs detected"
        elif obsolete_score >= 5:
            status = "WEAKENED"  # Build is weaker but playable
            recommendation = "CONSIDER ALTERNATIVES - Moderate nerfs"
        elif obsolete_score <= -5:
            status = "BUFFED"  # Build got stronger
            recommendation = "KEEP PLAYING - Build was buffed"
        else:
            status = "STABLE"  # No significant changes
            recommendation = "CONTINUE - No major changes"
        
        return {
            "hero": hero_name,
            "status": status,
            "obsolete_score": obsolete_score,
            "affected_talents": affected_talents,
            "recommendation": recommendation
        }
    
    def scan_player_builds(self, player_builds, season_start_date):
        """
        Scan all of a player's builds for obsolete status.
        
        Args:
            player_builds (list): List of build dicts with hero, talents, games, wr
            season_start_date (datetime): Season start date
            
        Returns:
            list: Analysis results for each build
        """
        results = []
        
        for build in player_builds:
            analysis = self.analyze_build(
                build['hero'],
                build['talents'],
                season_start_date
            )
            
            analysis['games_played'] = build['games']
            analysis['win_rate'] = build['win_rate']
            
            results.append(analysis)
        
        return results
    
    def generate_alert(self, obsolete_builds):
        """
        Generate a user-friendly alert for obsolete builds.
        
        Args:
            obsolete_builds (list): List of obsolete build analyses
            
        Returns:
            str: Formatted alert message
        """
        if not obsolete_builds:
            return "✅ All builds are up-to-date!"
        
        alert = "⚠️ **LEGACY BUILD ALERT** ⚠️\n\n"
        alert += "The following builds have been nerfed and may be obsolete:\n\n"
        
        for build in obsolete_builds:
            if build['status'] in ['OBSOLETE', 'WEAKENED']:
                alert += f"**{build['hero']}** ({build['games_played']} games, {build['win_rate']:.1f}% WR)\n"
                alert += f"Status: {build['status']} (Score: {build['obsolete_score']})\n"
                alert += f"Recommendation: {build['recommendation']}\n"
                
                for talent in build['affected_talents']:
                    alert += f"  - {talent['talent']} (L{talent['tier']}): {talent['change_type'].upper()} - {talent['description']}\n"
                
                alert += "\n"
        
        return alert


# Example usage
if __name__ == "__main__":
    # Initialize
    patch_monitor = PatchMonitor()
    detector = ObsoleteBuildDetector(patch_monitor)
    
    # Example: Check Gazlowe Build A
    gazlowe_build_a = {
        "hero": "Gazlowe",
        "talents": {
            1: "Big Game Hunter",
            4: "Rock It Sock It",
            7: "Goblin Fusion",
            10: "Grav-O-Bomb 3000",
            13: "Superior Schematics",
            16: "Firin' Mah Lazorz",
            20: "It's Raining Scrap"
        },
        "games": 72,
        "win_rate": 58.33
    }
    
    season_start = datetime(2025, 9, 1)  # Season 3 2025 start
    
    analysis = detector.analyze_build(
        gazlowe_build_a['hero'],
        gazlowe_build_a['talents'],
        season_start
    )
    
    print(json.dumps(analysis, indent=2))

