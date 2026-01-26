"""
AI Data Helper - Provides same data access as the AI system
Use this when responding directly to ensure same intelligence sources

USAGE:
    from scripts.ai_data_helper import get_helper
    helper = get_helper()
    
    # Get hero recommendations for a map/role
    healers = helper.get_role_recommendations('Garden of Terror', 'Healer', require_owned=False)
    
    # Get hero map stats
    stats = helper.get_hero_map_stats('Kharazim', 'Garden of Terror')
    
    # Get social intelligence
    social = helper.get_social_intelligence()
    
    # Get global meta WR
    meta_wr = helper.get_global_meta_wr('Deckard')
"""
from database_manager import DatabaseManager
import json

class AIDataHelper:
    def __init__(self):
        self.db = DatabaseManager()
        self._load_cache()
    
    def _load_cache(self):
        """Load same data as CACHE in api_server.py"""
        # Player Profile
        self.profile = self.db.get_kv('player_profile') or {}
        
        # Player Interactions
        self.interactions = self.db.get_kv('player_interactions') or {}
        
        # Hero Roles
        self.hero_roles = self.db.get_kv('hero_roles') or {}
        
        # Global Meta
        with self.db._get_connection() as conn:
            rows = conn.execute('SELECT * FROM global_meta_stats').fetchall()
            self.global_meta = [dict(r) for r in rows]
            for hero in self.global_meta:
                hero['name'] = hero['hero']  # Frontend compatibility
                hero['builds'] = json.loads(hero['builds_json']) if hero.get('builds_json') else []
        
        # Config
        config = self.db.get_kv('cerebrate_config') or {}
        self.banned_heroes = set(config.get('roster_constraints', {}).get('global_bans', []))
        
        # Roster
        roster_data = self.db.get_kv('hero_roster_levels') or {}
        self.owned_heroes = set(roster_data.get('heroes', {}).keys())
        self.hero_levels = roster_data.get('heroes', {})
        
        # Mission Cache
        mission_cache_raw = self.db.get_kv('map_recommendations_cache') or {}
        self.mission_cache = mission_cache_raw.get('recommendations', {})
    
    def get_hero_map_stats(self, hero, map_name):
        """Get hero performance on specific map from player profile"""
        hero_stats = self.profile.get('hero_map_stats', {}).get(hero, {})
        
        # Check season_2025_3 and lifetime
        for map_data in hero_stats.get('season_2025_3', []) + hero_stats.get('lifetime', []):
            if map_data.get('game_map') == map_name:
                return {
                    'wr': float(map_data.get('win_rate', 0)),
                    'games': map_data.get('games_played', map_data.get('games', 0)),
                    'source': map_data.get('source', 'Historical')
                }
        
        # Fallback to database
        db_stats = self.db.get_hero_map_stats(hero)
        for stat in db_stats:
            if stat['map'] == map_name:
                return {
                    'wr': stat['win_rate'],
                    'games': stat['games_played'],
                    'source': 'Replay Archive'
                }
        
        return None
    
    def get_global_meta_wr(self, hero):
        """Get global meta win rate for hero"""
        for hero_meta in self.global_meta:
            if hero_meta.get('hero') == hero or hero_meta.get('name') == hero:
                return hero_meta.get('win_rate', 0)
        return None
    
    def get_role_recommendations(self, map_name, role, require_owned=True):
        """Get hero recommendations for role on map (same logic as AI)
        
        Args:
            map_name: Map to check
            role: Hero role (Healer, Tank, etc.)
            require_owned: If False, show all heroes with data even if not in roster
        """
        hero_to_role = {}
        for r, heroes in self.hero_roles.items():
            for hero in heroes:
                hero_to_role[hero] = r
        
        candidates = []
        
        # 1. Check profile hero_map_stats
        for hero, stats in self.profile.get('hero_map_stats', {}).items():
            if hero in self.banned_heroes:
                continue
            if require_owned and hero not in self.owned_heroes:
                continue
            if hero_to_role.get(hero) != role:
                continue
            
            for map_data in stats.get('season_2025_3', []) + stats.get('lifetime', []):
                if map_data.get('game_map') == map_name:
                    wr = float(map_data.get('win_rate', 0))
                    games = map_data.get('games_played', map_data.get('games', 0))
                    if games >= 1:
                        candidates.append({
                            'hero': hero,
                            'wr': wr,
                            'games': games,
                            'stats': {'winRate': wr, 'games': games},
                            'reason': f'{wr:.1f}% WR on {map_name} ({games} games)',
                            'source': map_data.get('source', 'Historical'),
                            'has_player_data': True
                        })
                    break
        
        # 2. Supplement with database
        try:
            with self.db._get_connection() as conn:
                rows = conn.execute('SELECT DISTINCT hero FROM matches WHERE map = ?', (map_name,)).fetchall()
                all_heroes_in_db = {row['hero'] for row in rows if row['hero']}
            
            for hero in all_heroes_in_db:
                if hero in self.banned_heroes:
                    continue
                if require_owned and hero not in self.owned_heroes:
                    continue
                if hero_to_role.get(hero) != role:
                    continue
                
                # Check if already added
                if any(c['hero'] == hero for c in candidates):
                    continue
                
                db_map_stats = self.db.get_hero_map_stats(hero)
                for stat in db_map_stats:
                    if stat['map'] == map_name:
                        wr = stat['win_rate']
                        games = stat['games_played']
                        if games >= 1:
                            candidates.append({
                                'hero': hero,
                                'wr': wr,
                                'games': games,
                                'stats': {'winRate': wr, 'games': games},
                                'reason': f'{wr:.1f}% WR on {map_name} ({games} games)',
                                'source': 'Replay Archive',
                                'has_player_data': True
                            })
                        break
        except:
            pass
        
        # 3. Fill with owned heroes that have global meta but no map data
        hero_to_role = {}
        for r, heroes in self.hero_roles.items():
            for hero in heroes:
                hero_to_role[hero] = r
        
        # 4. Fill with heroes that have global meta but no map data
        # Check all heroes for this role (owned or in profile)
        heroes_to_check = set(self.owned_heroes) if require_owned else set()
        # Also include heroes from profile
        for hero in self.profile.get('hero_map_stats', {}).keys():
            heroes_to_check.add(hero)
        
        for hero in heroes_to_check:
            if hero in self.banned_heroes:
                continue
            if hero_to_role.get(hero) != role:
                continue
            if any(c['hero'] == hero for c in candidates):
                continue
            
            # If no map data but has global meta, include it
            meta_wr = self.get_global_meta_wr(hero)
            if meta_wr and len(candidates) < 5:
                candidates.append({
                    'hero': hero,
                    'wr': meta_wr,
                    'games': 0,
                    'stats': {'winRate': meta_wr, 'games': 0},
                    'reason': f'{meta_wr:.1f}% WR (Meta)',
                    'source': 'Meta',
                    'has_player_data': False
                })
        
        # Sort by WR
        candidates.sort(key=lambda x: x['wr'] if x['has_player_data'] else -1, reverse=True)
        return candidates[:5]  # Top 5
    
    def get_social_intelligence(self):
        """Get social intelligence data"""
        strong_allies = []
        nemeses = []
        frequent_rivals = []
        
        for player_name, player_data in self.interactions.items():
            total_with = player_data.get('total_with', 0)
            total_against = player_data.get('total_against', 0)
            wins_with = player_data.get('wins_with', 0)
            wins_against = player_data.get('wins_against', 0)
            
            wr_with = (wins_with / total_with * 100) if total_with > 0 else 0
            wr_against = (wins_against / total_against * 100) if total_against > 0 else 0
            
            if total_with >= 3 and wr_with >= 60:
                strong_allies.append({
                    'name': player_name,
                    'wr': wr_with,
                    'games': total_with
                })
            
            if total_against >= 3 and wr_against < 40:
                nemeses.append({
                    'name': player_name,
                    'wr': wr_against,
                    'games': total_against
                })
            
            if total_with >= 3 and total_against >= 3:
                frequent_rivals.append({
                    'name': player_name,
                    'wr_with': wr_with,
                    'games_with': total_with,
                    'wr_against': wr_against,
                    'games_against': total_against
                })
        
        strong_allies.sort(key=lambda x: x['wr'] * x['games'], reverse=True)
        nemeses.sort(key=lambda x: x['wr'] * x['games'])
        frequent_rivals.sort(key=lambda x: x['games_with'] + x['games_against'], reverse=True)
        
        return {
            'strong_allies': strong_allies[:5],
            'nemeses': nemeses[:5],
            'frequent_rivals': frequent_rivals[:3]
        }
    
    def validate_ai_recommendation(self, map_name, role, ai_hero, ai_wr=None):
        """Validate AI's recommendation against helper's data
        
        Returns dict with:
        - valid: bool - Does hero exist and have data?
        - expected_wr: float - What WR should be shown?
        - expected_source: str - What source tag should be used?
        - rank: int - Where does this hero rank among options?
        - better_options: list - Heroes with higher WR that weren't recommended
        """
        recommendations = self.get_role_recommendations(map_name, role, require_owned=False)
        
        # Find the AI's hero in our recommendations
        hero_found = None
        for rec in recommendations:
            if rec['hero'] == ai_hero:
                hero_found = rec
                break
        
        result = {
            'valid': hero_found is not None,
            'expected_wr': None,
            'expected_source': None,
            'rank': None,
            'better_options': []
        }
        
        if hero_found:
            result['expected_wr'] = hero_found['wr']
            if hero_found['has_player_data']:
                source = hero_found['source']
                if 'lifetime' in str(source).lower():
                    result['expected_source'] = '[Lifetime]'
                elif 'season' in str(source).lower() or 's3' in str(source).lower():
                    result['expected_source'] = '[S3]'
                elif 'verified' in str(source).lower():
                    result['expected_source'] = '[Verified]'
                else:
                    result['expected_source'] = '[Historical]'
            else:
                result['expected_source'] = '[Meta]'
            
            # Find rank
            for i, rec in enumerate(recommendations, 1):
                if rec['hero'] == ai_hero:
                    result['rank'] = i
                    break
            
            # Find better options
            hero_wr = hero_found['wr'] if hero_found['has_player_data'] else hero_found.get('wr', 0) or 0
            for rec in recommendations:
                if rec['hero'] == ai_hero:
                    continue
                rec_wr = rec['wr'] if rec['has_player_data'] else rec.get('wr', 0) or 0
                if rec_wr > hero_wr:
                    result['better_options'].append({
                        'hero': rec['hero'],
                        'wr': rec_wr,
                        'source': '[Lifetime]' if rec['has_player_data'] and 'lifetime' in str(rec['source']).lower() else '[S3]' if rec['has_player_data'] and 'season' in str(rec['source']).lower() else '[Meta]' if not rec['has_player_data'] else '[Historical]'
                    })
        
        return result

# Global instance
_helper = None

def get_helper():
    """Get singleton instance"""
    global _helper
    if _helper is None:
        _helper = AIDataHelper()
    return _helper
