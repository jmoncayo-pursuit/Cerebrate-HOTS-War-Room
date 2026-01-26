#!/usr/bin/env python3
"""
API server for AI chat using Gemini API
"""

# Suppress warnings FIRST, before any other imports
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*google.generativeai.*")
warnings.filterwarnings("ignore", message=".*All support for the.*")

import os
import json
import io
import logging
from datetime import datetime

# Suppress Flask/Werkzeug startup messages BEFORE importing Flask
logging.getLogger('werkzeug').setLevel(logging.ERROR)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv() # Load env vars from .env file
import time

import google.generativeai as genai
import PIL.Image

# Audit Imports
from src.audit.heroes_profile import HeroesProfileClient
from src.audit.analyzer import AuditEngine
from api.logger import ColoredLogger
from database_manager import DatabaseManager

app = Flask(__name__)
CORS(app)

# Initialize Database
DB = DatabaseManager()

# Suppress Flask's default request logging (reduces terminal spam)
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)  # Only show errors, not every request

ColoredLogger.setup_flask_logging(app, "API")

@app.route('/api/data/<path:filename>')
def serve_data_file(filename):
    """Serve data from SQL KV store with file fallback"""
    # 1. SQL Master Check for JSON
    if filename.endswith('.json'):
        # Normalize key (e.g., 'heroes/thebutcher.json' -> 'heroes_thebutcher')
        key = filename.replace('.json', '').replace('/', '_').replace('\\', '_')
        
        # Special case for global stats table
        if key == 'global_hero_stats_stormleague_plus_talents':
            with DB._get_connection() as conn:
                rows = conn.execute('SELECT * FROM global_meta_stats').fetchall()
                if rows:
                    data = []
                    for r in rows:
                        d = dict(r)
                        d['name'] = d.get('hero') # Compatibility
                        d['builds'] = json.loads(d['builds_json']) if d.get('builds_json') else []
                        data.append(d)
                    return jsonify(data)

        data = DB.get_kv(key)
        if data is not None:
            return jsonify(data)
            
    # 2. Physical File Fallback
    filepath = os.path.join('src', 'data', filename)
    if os.path.exists(filepath):
        return send_from_directory('src/data', filename)
            
    return jsonify({'error': 'File not found'}), 404

# Learning Coach Routes
from api.advice_routes import advice_bp
from api.war_room_routes import war_room_bp
from api.data_sources_routes import data_sources_bp
app.register_blueprint(advice_bp)
app.register_blueprint(war_room_bp)
app.register_blueprint(data_sources_bp)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    ColoredLogger.warn("GEMINI_API_KEY not found in environment variables.", "API")
genai.configure(api_key=GEMINI_API_KEY)
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash') # High-speed default
GEMINI_API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent'

# --- TACTICAL BREADCRUMBS ---
PIPELINE_VERSION = "2.1.0" # Major logic updates: BoE Immortal Dmg + Summary constraints
LAST_ACTUAL_MODEL = "unknown"
TACTICAL_LINK_LEVEL = "Standard" # Standard, Stable, Fast, Override
ORCHESTRATOR = None

# Free Tier Protection
from quota_manager import QuotaManager
QUOTA = QuotaManager()

# --- CACHE MECHANISM ---
class ContextCache:
    def __init__(self):
        self.brain_protocol = ""
        self.granular_training = ""
        self.social_intelligence = ""
        self.verified_data = ""
        self.player_profile = {}
        self.player_interactions = {}
        self.hero_roles = {}
        self.global_meta = []
        self.map_stats = {}
        self.last_loaded = 0

    def load_all(self):
        ColoredLogger.signal("CACHE", "Initializing Neural Context Matrix...")
        start_t = time.time()

        # 1. Brain Protocol
        try:
            if os.path.exists('.agent/brain/AI_CHAT_PROTOCOL.md'):
                with open('.agent/brain/AI_CHAT_PROTOCOL.md', 'r') as f:
                    self.brain_protocol = f.read()
        except Exception as e:
            ColoredLogger.error(f"Cache Error (Protocol): {e}", "API")
        
        # 1.5 Granular Excellence Training
        try:
            if os.path.exists('.agent/brain/GRANULAR_EXCELLENCE_TRAINING.md'):
                with open('.agent/brain/GRANULAR_EXCELLENCE_TRAINING.md', 'r') as f:
                    self.granular_training = f.read()
        except Exception as e:
            ColoredLogger.error(f"Cache Error (Training): {e}", "API")
        
        # 1.6 Draft Recommendation Protocol
        try:
            if os.path.exists('.agent/brain/DRAFT_RECOMMENDATION_PROTOCOL.md'):
                with open('.agent/brain/DRAFT_RECOMMENDATION_PROTOCOL.md', 'r') as f:
                    self.draft_protocol = f.read()
            else:
                self.draft_protocol = ""
        except Exception as e:
            ColoredLogger.error(f"Cache Error (Draft Protocol): {e}", "API")
            self.draft_protocol = ""
        
        # 1.7 Social Intelligence Protocol
        try:
            if os.path.exists('.agent/brain/SOCIAL_INTELLIGENCE_PROTOCOL.md'):
                with open('.agent/brain/SOCIAL_INTELLIGENCE_PROTOCOL.md', 'r') as f:
                    self.social_intelligence = f.read()
        except Exception as e:
            ColoredLogger.error(f"Cache Error (Social): {e}", "API")
        
        # 2. Project Memory (Master Context)
        try:
            if os.path.exists('.agent/PROJECT_MEMORY.md'):
                with open('.agent/PROJECT_MEMORY.md', 'r') as f:
                    self.verified_data = f.read()
        except Exception as e:
            ColoredLogger.error(f"Cache Error (Memory): {e}", "API")

        # 2.5 Cerebrate Social Template
        try:
            if os.path.exists('.agent/brain/CEREBRATE_SOCIAL_INTEL_TEMPLATE.md'):
                with open('.agent/brain/CEREBRATE_SOCIAL_INTEL_TEMPLATE.md', 'r') as f:
                    self.cerebrate_template = f.read()
            else:
                self.cerebrate_template = ""
        except Exception as e:
            ColoredLogger.error(f"Cache Error (Template): {e}", "API")

        # 3. Player Profile
        self.player_profile = DB.get_kv('player_profile') or {}
        
        # 3.5 Player Interactions
        self.player_interactions = DB.get_kv('player_interactions') or {}
        
        # 3.5.1 Load Neural Intelligence Briefs and attach to player interactions
        neural_briefs = DB.get_kv('neural_intelligence_briefs') or {}
        for player_id, brief in neural_briefs.items():
            if player_id in self.player_interactions:
                self.player_interactions[player_id]['aiStrategy'] = brief
        
        # 3.6 Hero Roles & Data
        self.hero_roles = DB.get_kv('hero_roles') or {}
        self.hero_data = DB.get_kv('hero_data') or {}
        self.talents = DB.get_kv('talents') or {}
            
        # 4. Global Meta
        # Load from table instead of big JSON
        with DB._get_connection() as conn:
            rows = conn.execute('SELECT * FROM global_meta_stats').fetchall()
            self.global_meta = [dict(r) for r in rows]
            # Unpack builds_json
            for hero in self.global_meta:
                hero['name'] = hero['hero'] # Frontend compatibility
                hero['builds'] = json.loads(hero['builds_json']) if hero.get('builds_json') else []

        # 5. Config
        config = DB.get_kv('cerebrate_config') or {}
        self.map_stats = {
            's3': config.get('map_performance_s3', {}),
            'strategies': config.get('strategies', {}),
            'constraints': config.get('roster_constraints', {})
        }

        # 6. Mission Cache
        mission_cache_raw = DB.get_kv('map_recommendations_cache') or {}
        self.mission_cache = mission_cache_raw.get('recommendations', {})

        self.last_loaded = time.time()
        ColoredLogger.success(f"Context Matrix loaded from SQLite ({self.last_loaded - start_t:.4f}s)")

# Global Cache Instance
CACHE = ContextCache()

# Initialize cache on startup (lazy load or immediate)
# We'll do it on first request or if explicitly called
if not CACHE.last_loaded:
    CACHE.load_all()

# --- RESPONSE CACHE MECHANISM ---
class ResponseCache:
    def __init__(self):
        self.cache_file = 'src/data/response_cache.json'
        self.cache = {}
        self.player_hash = None
        self.warmed = False  # Track if cache has been warmed
        self.load()
    
    def _get_player_hash(self):
        """Generate hash of player profile to detect changes"""
        import hashlib
        profile = CACHE.player_profile
        # Hash based on wins, rank, and last match date
        data = f"{profile.get('rank_data', {}).get('storm_league', {}).get('season_2025_3', {}).get('wins', 0)}"
        data += f"{profile.get('rank_data', {}).get('storm_league', {}).get('current_rank', '')}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def load(self):
        """Load cache from disk if valid"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    if self._is_valid(data):
                        self.cache = data.get('responses', {})
                        self.player_hash = data.get('player_hash')
                        ColoredLogger.info(f"Response cache loaded ({len(self.cache)} entries)", "CACHE")
                        if not self.cache:
                            self.warm_cache()
                    else:
                        # Silenced for demo - standard behavior when session stats update
                        self.player_hash = self._get_player_hash()
                        self.cache = {}
                        self.warm_cache()
            except Exception as e:
                ColoredLogger.error(f"Cache load error: {e}", "CACHE")
    
    def _is_valid(self, data):
        """Check if cache is still valid"""
        if not data.get('player_hash'):
            return False
        current_hash = self._get_player_hash()
        return data.get('player_hash') == current_hash
    
    def get(self, query_key):
        """Get cached response for query"""
        normalized = self._normalize_key(query_key)
        return self.cache.get(normalized, {}).get('response')
    
    def set(self, query_key, response):
        """Set cached response"""
        from datetime import datetime
        normalized = self._normalize_key(query_key)
        self.cache[normalized] = {
            'query': query_key,
            'response': response,
            'generated_at': datetime.now().isoformat()
        }
    
    def save(self):
        """Save cache to disk"""
        from datetime import datetime
        data = {
            'version': '1.0',
            'generated_at': datetime.now().isoformat(),
            'player_hash': self._get_player_hash(),
            'responses': self.cache
        }
        with open(self.cache_file, 'w') as f:
            json.dump(data, f, indent=2)
        ColoredLogger.info(f"Response cache saved ({len(self.cache)} entries)", "CACHE")
    
    def _normalize_key(self, query):
        """Normalize query to cache key"""
        return query.lower().replace(' ', '_').replace("'", '')
    
    def warm_cache(self):
        """Pre-generate responses for all maps"""
        maps = [
            'Infernal Shrines', 'Battlefield of Eternity', 'Dragon Shire',
            "Blackheart's Bay", 'Sky Temple', 'Tomb of the Spider Queen',
            'Alterac Pass', 'Volskaya Foundry', 'Garden of Terror',
            'Cursed Hollow', 'Towers of Doom', 'Braxis Holdout',
            'Hanamura Temple', 'Warhead Junction'
        ]
        
        # ACTIVE: Prioritize Real-Time Intelligence by pre-calculating it
        for map_name in maps:
           if not self.get(map_name):
               response = self._generate_map_response(map_name, role_filter=None)
               self.set(map_name, response)
        
        self.save()
        ColoredLogger.success(f"Mission Cache ready ({len(maps)} maps pre-calculated)", "CACHE")
    
    def _extract_bans_for_map(self, map_name):
        """Parse BAN_RECOMMENDATIONS.md for specific map bans"""
        try:
            ban_path = '.agent/brain/BAN_RECOMMENDATIONS.md'
            if not os.path.exists(ban_path): return "No Ban Doctrine Found."
            
            with open(ban_path, 'r') as f:
                content = f.read()
            
            # Regex to find header like "### Infernal Shrines (Your 70.6% WR Map)"
            import re
            map_name_esc = re.escape(map_name)
            # Match "### [MapName]..." until the next "### " or End of File
            match = re.search(f"### {map_name_esc}.*?\\n(.*?)(?:\\n### |\\Z)", content, re.DOTALL | re.IGNORECASE)
            
            if not match:
                return "Universal Bans: Tracer, Genji, Maiev"
            
            section = match.group(1)
            
            # Extract Priority Bans list
            bans = []
            lines = section.split('\n')
            capture = False
            for line in lines:
                if "**Priority Bans**" in line:
                    capture = True
                    continue
                if capture:
                    # Look for numbered list: "1. **Hero**"
                    if line.strip() and (line.strip()[0].isdigit() and line.strip()[1] == '.'):
                         # Extract clean text: "1. **Kael'thas** ... - Why: ..."
                         # We want "**Kael'thas**" or full text. Let's get the bold hero name.
                         b_match = re.search(r"\*\*(.*?)\*\*", line)
                         if b_match:
                             bans.append(f"**{b_match.group(1)}**") # Keep bold formatting
                         else:
                             # Fallback, just take the whole line cleaned
                             clean_line = line.split('.', 1)[1].strip()
                             bans.append(clean_line)
                    elif line.strip() == "" and len(bans) > 0:
                        continue # Skip empty lines inside list
                    elif "Acceptable Bans" in line or "---" in line:
                        break # Stop at next section
            
            return ", ".join(bans[:3]) if bans else "Universal Bans: Tracer, Genji, Maiev"
        except Exception as e:
            return f"Error extraction bans: {e}"

    def _get_best_heroes_for_map(self, map_name):
        """Get Primary and Backup heroes for EACH role, sorted by Primary WR"""
        try:
             profile = CACHE.player_profile or {}
             
             # Get owned heroes
             roster_data = DB.get_kv('hero_roster_levels') or {}
             owned_heroes = set(roster_data.get('heroes', {}).keys())
             
             role_groups = {role: [] for role in ['Tank', 'Healer', 'Ranged Assassin', 'Bruiser']}
             stats = profile.get('hero_map_stats', {})
             
             # Need roles mapping
             roles_map = CACHE.hero_roles
             hero_to_role = {}
             if roles_map:
                 for role, heroes in roles_map.items():
                     for h in heroes:
                         hero_to_role[h] = role
             
             # 1. Fill from Personal Data - USE THE EXPLICIT LIST OF HEROES YOU PLAY
             # Get heroes from hero_preferences (the definitive list of heroes you actually play)
             hero_prefs = profile.get('hero_preferences', {})
             played_heroes = set()
             
             # EXCLUDE heroes you've explicitly said you would never play
             excluded_heroes = set()
             excluded_heroes.update(hero_prefs.get('dislike', []))  # Heroes you dislike/never play
             excluded_heroes.update(hero_prefs.get('rarely_play', []))  # Heroes you rarely play
             
             # Preferred heroes (main heroes you play)
             for hero_obj in hero_prefs.get('preferred_heroes', []):
                 if isinstance(hero_obj, dict):
                     hero_name = hero_obj.get('hero')
                     if hero_name and hero_name not in excluded_heroes:
                         played_heroes.add(hero_name)
                 elif isinstance(hero_obj, str) and hero_obj not in excluded_heroes:
                     played_heroes.add(hero_obj)
             
             # Conditional picks (heroes you play sometimes)
             for hero_obj in hero_prefs.get('conditional_picks', []):
                 if isinstance(hero_obj, dict):
                     hero_name = hero_obj.get('hero')
                     if hero_name and hero_name not in excluded_heroes:
                         played_heroes.add(hero_name)
                 elif isinstance(hero_obj, str) and hero_obj not in excluded_heroes:
                     played_heroes.add(hero_obj)
             
             # Reluctant picks (heroes you can play but don't prefer)
             for hero_obj in hero_prefs.get('reluctant_picks', []):
                 if isinstance(hero_obj, dict):
                     hero_name = hero_obj.get('hero')
                     if hero_name and hero_name not in excluded_heroes:
                         played_heroes.add(hero_name)
                 elif isinstance(hero_obj, str) and hero_obj not in excluded_heroes:
                     played_heroes.add(hero_obj)
             
             # Fallback: if no hero_preferences, use heroes from hero_stats (but still exclude disliked/rarely_play)
             hero_stats_all = profile.get('hero_stats', {})
             if not played_heroes:
                 for hero, hero_data in hero_stats_all.items():
                     if hero in excluded_heroes:
                         continue  # Skip excluded heroes
                     lifetime = hero_data.get('verified_lifetime', {})
                     season = hero_data.get('verified_season_2025_3', {})
                     if (lifetime.get('games', 0) > 0 or season.get('games', 0) > 0):
                         played_heroes.add(hero)
             
             # Use ONLY heroes from your explicit list (excluding never-play heroes)
             available_heroes = played_heroes if played_heroes else (owned_heroes - excluded_heroes)
             
             # Filter owned heroes to only include heroes you actually play AND exclude never-play heroes
             if played_heroes:
                 owned_heroes = owned_heroes.intersection(played_heroes) if owned_heroes else played_heroes
             owned_heroes = owned_heroes - excluded_heroes  # Remove excluded heroes
             
             for hero, map_data in stats.items():
                 # Skip if excluded (dislike/rarely_play)
                 if hero in excluded_heroes:
                     continue
                 # Skip if not owned AND not played
                 if available_heroes and hero not in available_heroes:
                     continue
                     
                 role = hero_to_role.get(hero)
                 if role not in role_groups:
                     continue 
                 # Check Lifetime and Season
                 relevant = map_data.get('lifetime', []) + map_data.get('season_2025_3', [])
                 for entry in relevant:
                     if entry.get('game_map') == map_name:
                         games = int(entry.get('games_played', 0) or 0)
                         wr = float(entry.get('win_rate', 0))
                         # Filter: minimum 3 games AND 45%+ WR (don't recommend losing builds)
                         if games >= 3 and wr >= 45.0:
                             role_groups[role].append({
                                 'hero': hero,
                                 'wr': wr,
                                 'games': games,
                                 'source': str(entry.get('source', 'Record') or 'Record')
                             })
                         break
             
             # 2. Fill Gaps with Meta Picks (Dynamic) - Only owned heroes
             # DYNAMIC META LOOKUP (No Hardcoded Lists)
             map_meta = {} # We will now query the DB/Cache dynamically
             
             # Filter global meta by role to create dynamic suggestion lists
             global_meta_by_role = {}
             if CACHE.global_meta:
                 for h_meta in CACHE.global_meta:
                     h_name = h_meta.get('hero') or h_meta.get('name')
                     h_role = hero_to_role.get(h_name) # Use our role mapping
                     if h_role:
                         if h_role not in global_meta_by_role:
                             global_meta_by_role[h_role] = []
                         global_meta_by_role[h_role].append(h_name)
             
             # Use global meta (role-based) as the "meta picks" source
             map_meta = global_meta_by_role
             for role in role_groups:
                 if len(role_groups[role]) < 2: # Need at least Primary + Backup
                     needed = 2 - len(role_groups[role])
                     
                     # First, try to find other heroes from your roster that you've played (even without map-specific data)
                     # Prioritize heroes from your roster list
                     roster_played = owned_heroes.intersection(played_heroes) if owned_heroes else played_heroes
                     for hero in roster_played:
                         if needed <= 0: break
                         hero_role = hero_to_role.get(hero)
                         if hero_role != role:
                             continue
                         # Check if already present
                         if not any(x['hero'] == hero for x in role_groups[role]):
                             # Check if hero has any stats at all
                             hero_data = hero_stats_all.get(hero, {})
                             lifetime = hero_data.get('verified_lifetime', {})
                             season = hero_data.get('verified_season_2025_3', {})
                             total_games = lifetime.get('games', 0) + season.get('games', 0)
                             
                             if total_games > 0:
                                 wr = lifetime.get('win_rate', lifetime.get('wr', 50)) or season.get('win_rate', season.get('wr', 50)) or 50
                                 # Only recommend if WR is decent (45%+) - don't recommend heroes you play poorly
                                 if float(wr) >= 45.0:
                                     role_groups[role].append({
                                         'hero': hero,
                                         'wr': float(wr),
                                         'games': total_games,
                                         'source': 'Your Stats (All Maps)'
                                     })
                                     needed -= 1
                     
                     # Only use meta picks if still needed AND hero is owned/played AND not excluded
                     # BUT: Only if user has NO heroes with stats for this role (don't recommend heroes with no stats)
                     meta_options = map_meta.get(role, [])
                     # Check if we already have heroes with actual stats (games > 0)
                     has_stats = any(x.get('games', 0) > 0 for x in role_groups[role])
                     
                     # Only use meta picks if:
                     # 1. We have NO heroes with stats for this role, OR
                     # 2. The meta hero is owned/played AND has some stats (even if not map-specific)
                     for mh in meta_options:
                        if needed <= 0: break
                        # Skip excluded heroes (dislike/rarely_play)
                        if mh in excluded_heroes:
                            continue
                        # Only add if owned OR played
                        if available_heroes and mh not in available_heroes:
                            continue
                         # Check if already present
                        if any(x['hero'] == mh for x in role_groups[role]):
                            continue
                        
                        # If we already have heroes with stats, skip meta picks (user wants stats-based recs)
                        if has_stats:
                            continue
                        
                        # Check if meta hero has any stats at all (even if not map-specific)
                        hero_data = hero_stats_all.get(mh, {})
                        lifetime = hero_data.get('verified_lifetime', {})
                        season = hero_data.get('verified_season_2025_3', {})
                        total_games = lifetime.get('games', 0) + season.get('games', 0)
                        
                        # Only add meta pick if user has stats for this hero (even if not map-specific)
                        if total_games > 0:
                            wr = lifetime.get('win_rate', lifetime.get('wr', 50)) or season.get('win_rate', season.get('wr', 50)) or 50
                            role_groups[role].append({
                                'hero': mh,
                                'wr': float(wr),
                                'games': total_games,
                                'source': 'Your Stats (All Maps)'
                            })
                            needed -= 1
             
             # Compile Final Structure
             final_structure = []
             for role, candidates in role_groups.items():
                 # Sort by WR
                 candidates.sort(key=lambda x: x['wr'], reverse=True)
                 
                 
                 # Filter out heroes with 0 games (meta placeholders without stats)
                 # Double check to ensure we aren't showing heroes the user has never played
                 valid_candidates = []
                 for c in candidates:
                    if c.get('games', 0) > 0:
                        valid_candidates.append(c)
                 
                 primary = valid_candidates[0] if valid_candidates else None
                 backup = valid_candidates[1] if len(valid_candidates) > 1 else None
                 
                 if primary:
                     final_structure.append({
                         'role': role,
                         'primary': primary,
                         'backup': backup
                     })
             
             # Sort roles by Primary WR
             final_structure.sort(key=lambda x: x['primary']['wr'], reverse=True)
             return final_structure
        except Exception as e:
            ColoredLogger.error(f"Error getting role champions: {e}")
            return []

    def _generate_map_response(self, map_name, role_filter=None):
        """Generate response for a specific map using LOCAL Intelligence (Speedy Prep)"""
        try:
            # 1. Get Bans
            bans_str = self._extract_bans_for_map(map_name)
            
            # 2. Get Heroes (Structured) - This already filters by owned heroes
            recommendations = self._get_best_heroes_for_map(map_name)
            
            # 3. Load Strategies for Deep Insight (from SQLite)
            map_strategy = None
            try:
                # Get exclusion list from hero_preferences
                profile = CACHE.player_profile or {}
                hero_prefs = profile.get('hero_preferences', {})
                excluded_heroes = set(hero_prefs.get('dislike', []))
                excluded_heroes.update(hero_prefs.get('rarely_play', []))
                
                with DB._get_connection() as conn:
                    row = conn.execute('SELECT content_json FROM strategies WHERE key = ? AND category = ?', (map_name, 'map_strategy')).fetchone()
                    if row:
                        map_strategy = json.loads(row['content_json'])
                        
                        # Filter strategy by played heroes (games > 0) AND exclude disliked
                        hero_stats_all = profile.get('hero_stats', {})
                        
                        # Helper to check if played
                        def has_played(h_name):
                             h_data = hero_stats_all.get(h_name, {})
                             lifetime = h_data.get('verified_lifetime', {})
                             season = h_data.get('verified_season_2025_3', {})
                             return (lifetime.get('games', 0) + season.get('games', 0)) > 0

                        # Filter primary
                        if map_strategy.get('primary'):
                            primary_name = map_strategy['primary'].get('name')
                            if primary_name in excluded_heroes or not has_played(primary_name):
                                map_strategy['primary'] = None
                        
                        # Filter backups
                        if map_strategy.get('backups'):
                            map_strategy['backups'] = [
                                b for b in map_strategy['backups'] 
                                if b.get('name') not in excluded_heroes 
                                and has_played(b.get('name'))
                            ]
            except Exception as e:
                ColoredLogger.error(f"Error loading map strategy for {map_name}: {e}", "CACHE")
            
            # 4. Meta Lookup for Defaults
            meta_lookup = {}
            if CACHE.global_meta:
                for h in CACHE.global_meta:
                    meta_lookup[h['name']] = h
            
            # 5. Default Builds (Gap Filler)
            DEFAULT_BUILDS = {
                "Johanna": "T3122222", "Muradin": "T1211112", "Anub\'arak": "T1221212", "Stitches": "T1112113", "Garrosh": "T1211131",
                "Rehgar": "T1231211", "Malfurion": "T1221312", "Brightwing": "T2331321", "Lt. Morales": "T2121222", "Anduin": "T1111111", "Kharazim": "T1111111", "Li Li": "T1111111",
                "Raynor": "T1132112", "Valla": "T2321221", "Falstad": "T2221222", "Sylvanas": "T1111111", "Junkrat": "T1331322", "Zagara": "T3221222", "Nazeebo": "T1111111",
                "Gazlowe": "T1222324", "Malthael": "T2112114", "Sonya": "T1221222", "Dehaka": "T1111111", "Ragnaros": "T1211221",
                "Jaina": "T2221222", "Li-Ming": "T2221222", "Kael\'thas": "T2221222", "Tychus": "T1231214", "Greymane": "T2221222",
                "Mephisto": "T1111111", "Azmodan": "T1111111", "Lunara": "T1111111", "Tracer": "T1111111", "Genji": "T1111111",
                "Diablo": "T1111111", "Arthas": "T1111111", "Blaze": "T1111111", "Tyrael": "T1111111", "E.T.C.": "T1111111"
            }
            
            response = f"## {map_name}\n"
            shown_heroes = set()
            
            # Add map strategy description if available
            if map_strategy and map_strategy.get('desc'):
                response += f"**Directives**: {map_strategy['desc']}\n\n"
            else:
                response += f"**Directives**: Control the localized objective points.\n\n"
            
            # Always show bans (even with role filter)
            if bans_str:
                response += f"🚫 **TARGETED BANS**: {bans_str}\n\n"
            
            # Add strategy primary/backup recommendations if available (already filtered by exclusion list)
            # Only show if not filtering by role OR if the primary/backup matches the role filter
            if map_strategy and not role_filter:
                if map_strategy.get('primary'):
                    primary = map_strategy['primary']
                    # Double-check exclusion (should already be filtered, but safety check)
                    hero_prefs = profile.get('hero_preferences', {})
                    excluded = set(hero_prefs.get('dislike', []))
                    excluded.update(hero_prefs.get('rarely_play', []))
                    if primary['name'] not in excluded:
                        response += f"### 🎯 STRATEGIC PRIMARY\n"
                        response += f"**{primary['name']}** ({primary.get('role', 'Bruiser')})\n"
                        if primary.get('insight'):
                            response += f"> {primary['insight']}\n"
                        if primary.get('code'):
                            # Format as [T1234567,Hero] for BuildDisplay component
                            code = str(primary['code'])
                            if code.startswith('T') and not code.startswith('[T'):
                                code = code[1:]  # Remove T prefix
                            if not code.startswith('['):
                                response += f"`[T{code},{primary['name']}]`\n"
                            else:
                                response += f"`{code}`\n"
                        response += "\n"
                        shown_heroes.add(primary['name'])
                
                if map_strategy.get('backups'):
                    hero_prefs = profile.get('hero_preferences', {})
                    excluded = set(hero_prefs.get('dislike', []))
                    excluded.update(hero_prefs.get('rarely_play', []))
                    # Filter backups again (safety check)
                    valid_backups = [b for b in map_strategy['backups'] if b.get('name') not in excluded]
                    if valid_backups:
                        response += f"### 🔄 STRATEGIC BACKUPS\n"
                        for backup in valid_backups[:3]:  # Limit to 3
                            response += f"**{backup['name']}** ({backup.get('role', 'Assassin')})\n"
                            if backup.get('insight'):
                                response += f"> {backup['insight']}\n"
                            if backup.get('code'):
                                # Format as [T1234567,Hero] for BuildDisplay component
                                code = str(backup['code'])
                                if code.startswith('T') and not code.startswith('[T'):
                                    code = code[1:]  # Remove T prefix
                                if not code.startswith('['):
                                    response += f"`[T{code},{backup['name']}]`\n"
                                else:
                                    response += f"`{code}`\n"
                            shown_heroes.add(backup['name'])
                        response += "\n"
            
            if recommendations:
                for group in recommendations:
                    role = group['role']
                    # Skip if filtering by role and this doesn't match
                    if role_filter and role != role_filter:
                        continue
                    p = group['primary']
                    b = group['backup']
                    
                    # --- Primary Recommendation ---
                    # Skip heroes with no stats (0 games) - they shouldn't be in final_structure but double-check
                    if p.get('games', 0) == 0:
                        continue
                    
                    # Skip if already shown in Strategic section
                    if p['hero'] in shown_heroes:
                        continue
                    
                    response += f"\n[{role.upper()}]\n"
                    # Format: HERO (Source) - XX% WR
                    response += f"**{p['hero']}** ({p.get('source', 'S3')}) - {p['wr']:.1f}% WR ({p['games']} games)\n"
                    
                    # Strategy/Build Logic P - Check map strategy first
                    found_p_code = False
                    if map_strategy and map_strategy.get('primary') and map_strategy['primary'].get('name') == p['hero']:
                        # Hero matches the primary recommendation in map strategy
                        primary = map_strategy['primary']
                        if primary.get('insight'):
                            response += f"> 🛠️ **Plan**: {primary['insight']}\n"
                        if primary.get('code'):
                            # Format as [T1234567,Hero] for BuildDisplay component
                            code = str(primary['code'])
                            if code.startswith('T') and not code.startswith('[T'):
                                code = code[1:]  # Remove T prefix
                                response += f"`[T{code},{p['hero']}]`\n"
                            elif code.startswith('[T'):
                                response += f"`{code}`\n"
                            else:
                                response += f"`[T{code},{p['hero']}]`\n"
                            found_p_code = True
                    elif map_strategy and map_strategy.get('backups'):
                        # Check if hero is in backups
                        backup_match = next((bk for bk in map_strategy['backups'] if bk.get('name') == p['hero']), None)
                        if backup_match:
                            if backup_match.get('insight'):
                                response += f"> 🛠️ **Plan**: {backup_match['insight']}\n"
                            if backup_match.get('code'):
                                # Format as [T1234567,Hero] for BuildDisplay component
                                code = str(backup_match['code'])
                                if code.startswith('T') and not code.startswith('[T'):
                                    code = code[1:]  # Remove T prefix
                                    response += f"`[T{code},{p['hero']}]`\n"
                                elif code.startswith('[T'):
                                    response += f"`{code}`\n"
                                else:
                                    response += f"`[T{code},{p['hero']}]`\n"
                                found_p_code = True
                    
                    if not found_p_code:
                         meta_hero = meta_lookup.get(p['hero'])
                         if meta_hero and meta_hero.get('builds'):
                            best_build = sorted(meta_hero['builds'], key=lambda x: x['win_chance'], reverse=True)[0]
                            response += f"> **Meta Standard**: {best_build['win_chance']}% WR\n"
                            talent_code = str(best_build['talent_code'])
                            # Ensure format is [T1234567,Hero]
                            if talent_code.startswith('T') and not talent_code.startswith('[T'):
                                talent_code = talent_code[1:]  # Remove T prefix
                            if not talent_code.startswith('['):
                                response += f"`[T{talent_code},{p['hero']}]`\n"
                            else:
                                response += f"`{talent_code}`\n"
                         else:
                             # Use Default
                             def_code = DEFAULT_BUILDS.get(p['hero'], 'T0000000')
                             # Remove T prefix if present
                             if def_code.startswith('T'):
                                 def_code = def_code[1:]
                             
                             # Only show if we have a valid code (not T0000000)
                             if def_code != '0000000':
                                response += f"> Standard: `[T{def_code},{p['hero']}]`\n"

                    # --- Backup Recommendation ---
                    # Only show backup if it has stats (games > 0)
                    if b and b.get('games', 0) > 0:
                        response += f"_{b['hero']} (Alternative) - {b['wr']:.1f}% WR ({b['games']} games)_\n"
                        found_b_code = False
                        if map_strategy and map_strategy.get('backups'):
                            backup_match = next((bk for bk in map_strategy['backups'] if bk.get('name') == b['hero']), None)
                            if backup_match:
                                if backup_match.get('insight'):
                                    response += f"> Plan: {backup_match['insight']}\n"
                                if backup_match.get('code'):
                                    # Format as [T1234567,Hero] for BuildDisplay component
                                    code = str(backup_match['code'])
                                    if code.startswith('T') and not code.startswith('[T'):
                                        code = code[1:]  # Remove T prefix
                                        response += f"`[T{code},{b['hero']}]`\n"
                                    elif code.startswith('[T'):
                                        response += f"`{code}`\n"
                                    else:
                                        response += f"`[T{code},{b['hero']}]`\n"
                                    found_b_code = True
                        if not found_b_code:
                             meta_hero = meta_lookup.get(b['hero'])
                             if meta_hero and meta_hero.get('builds'):
                                best_build = sorted(meta_hero['builds'], key=lambda x: x['win_chance'], reverse=True)[0]
                                talent_code = str(best_build['talent_code'])
                                # Ensure format is [T1234567,Hero]
                                if talent_code.startswith('T') and not talent_code.startswith('[T'):
                                    talent_code = talent_code[1:]  # Remove T prefix
                                if not talent_code.startswith('['):
                                    response += f"> Standard: `[T{talent_code},{b['hero']}]`\n"
                                else:
                                    response += f"`{talent_code}`\n"
                             else:
                                 def_code = DEFAULT_BUILDS.get(b['hero'], 'T0000000')
                                 # Remove T prefix if present
                                 if def_code.startswith('T'):
                                     def_code = def_code[1:]
                                 
                                 if def_code != '0000000':
                                     response += f"> Standard: `[T{def_code},{b['hero']}]`\n"
                    
                    response += "\n"
            else:
                response += "No verified hero data for this map. Consult General Tier List.\n"
            
            return response.strip()

        except Exception as e:
            ColoredLogger.error(f"Failed to generate map response for {map_name}: {e}", "CACHE")
            return f"Strategic analysis for {map_name} is offline."

RESPONSE_CACHE = ResponseCache()

@app.route('/api/refresh_context', methods=['POST'])
def refresh_cache():
    CACHE.load_all()
    # Also re-warm the response cache to reflect new stats in Mission Cache
    RESPONSE_CACHE.warm_cache()
    return jsonify({"success": True, "message": "Context cache and mission data synchronized"})

def call_gemini_api(prompt, context=None, raw_mode=False, image_data=None, silent=False, model_override=None):
    """
    Calls the Gemini API using the provided prompt and optional image.
    Uses exponential backoff for 429 errors AND automatic tiered fallback.
    """
    global LAST_ACTUAL_MODEL, TACTICAL_LINK_LEVEL
    
    # 1. IDENTIFY TIERS (Internal Standard: Zero Failure)
    is_vision = image_data is not None
    
    if is_vision:
        # Vision/OCR Tiers (Prioritize 2.5-flash for speed/availability, then Pro for precision)
        tiers = [
            ("gemini-2.5-flash", "Fast Link"),
            ("gemini-1.5-pro", "Neural Link"),
            ("gemini-2.5-flash-lite", "Nexus Intelligence"),
            ("gemini-1.5-flash", "Residual Link"),
            ("gemini-1.5-flash-002", "Legacy Link"),
            ("gemini-3-pro", "Future Link"),
            ("gemini-2.5-pro", "Evolutionary Link")
        ]
    else:
        # Analysis/Chat Tiers - Prioritize 2.5-flash as the stable bedrock for high RPM
        tiers = [
            ("gemini-2.5-flash", "Fast Link"),
            ("gemini-2.5-flash-lite", "Nexus Intelligence"),
            ("gemini-1.5-pro", "Neural Link"),
            ("gemini-1.5-flash", "Residual Link"),
            ("gemini-1.5-flash-002", "Legacy Link"),
            ("gemini-3-pro", "Future Link"),
            ("gemini-2.5-pro", "Evolutionary Link")
        ]
    
    # If explicitly overridden, try that first
    if model_override:
        # Check if already in tiers to avoid duplicates
        if not any(t[0] == model_override for t in tiers):
            tiers = [(model_override, "Modified")] + tiers
        else:
            # Reorder to put override first
            tgt = [t for t in tiers if t[0] == model_override][0]
            tiers.remove(tgt)
            tiers = [tgt] + tiers

    if not GEMINI_API_KEY:
        return "GEMINI_API_KEY missing. Please set it in your environment."
    
    import requests
    import time
    import base64

    # EARLY EXIT FOR RAW MODE (OCR, Extraction, Metadata)
    if raw_mode:
        if image_data:
            # We still need to process images for vision calls
            pass 
        else:
            # Standard fast-path
            full_prompt = prompt
            # Skip all the heavy context loading
            # We'll jump to the model execution loop
            pass
    
    p_low = prompt.lower()
    no_numbers_mode = any(k in p_low for k in ["no numbers", "no stats", "fucking numbers", "don't numbers", "dont numbers", "without stats"])
    
    p_clean = p_low.replace(' ', '').replace("'", "")
    map_keywords = {
        'infernalshrines': 'Infernal Shrines',
        'battlefieldofeternity': 'Battlefield of Eternity',
        'boe': 'Battlefield of Eternity',
        'dragonshire': 'Dragon Shire',
        'blackheartsbay': "Blackheart's Bay",
        'blackhearts': "Blackheart's Bay",
        'skytemple': 'Sky Temple',
        'tombofthespiderqueen': 'Tomb of the Spider Queen',
        'tomb': 'Tomb of the Spider Queen',
        'alteracpass': 'Alterac Pass',
        'alterac': 'Alterac Pass',
        'volskayafoundry': 'Volskaya Foundry',
        'volskaya': 'Volskaya Foundry',
        'gardenofterror': 'Garden of Terror',
        'garden': 'Garden of Terror',
        'cursedhallow': 'Cursed Hollow',
        'cursed': 'Cursed Hollow',
        'towersofdoom': 'Towers of Doom',
        'towers': 'Towers of Doom',
        'braxisholdout': 'Braxis Holdout',
        'braxis': 'Braxis Holdout',
        'hanamuratemple': 'Hanamura Temple',
        'hanamura': 'Hanamura Temple',
        'warheadjunction': 'Warhead Junction',
        'warhead': 'Warhead Junction'
    }
    
    detected_map = None
    for keyword, map_name in map_keywords.items():
        if keyword in p_clean:
            detected_map = map_name
            break

    # GREETING DETECTION (Prevent random recommendations)
    words = p_low.split()
    is_greeting = len(words) <= 3 and any(k in words for k in ["hi", "hello", "hey", "sup", "yo", "greetings"])
    
    # ROLE DETECTION (for filtering recommendations)
    detected_role = None
    role_keywords = {
        'healer': 'Healer',
        'healers': 'Healer',
        'support': 'Healer',
        'tank': 'Tank',
        'tanks': 'Tank',
        'bruiser': 'Bruiser',
        'bruisers': 'Bruiser',
        'melee': 'Bruiser',
        'ranged': 'Ranged Assassin',
        'ranged assassin': 'Ranged Assassin',
        'assassin': 'Ranged Assassin',
        'dps': 'Ranged Assassin'
    }
    for keyword, role in role_keywords.items():
        if keyword in p_low:
            detected_role = role
            break
    
    # INTENT DETECTION (Cerebrate Precision)
    is_draft_query = any(k in p_low for k in ["pick", "who", "draft", "recommend", "solo", "tank", "healer", "bruiser", "for", "prediction", "tips", "screenshot", "image", "map"]) or (detected_map is not None)
    is_post_match = any(k in p_low for k in ["why", "lose", "win", "what happened", "analysis", "mistake"])
    is_streak_query = any(k in p_low for k in ["streak", "loss", "win", "recent games", "history", "stuck"])
    is_forensic_audit = is_streak_query or is_post_match or any(k in p_low for k in ["audit", "report", "comprehensive"])
    
    # HERO BUILD DETECTION
    detected_hero = None
    is_build_query = any(k in p_low for k in ["build", "spec", "talent", "best", "optimal"])
    
    if is_build_query:
        # Check for hero names in the query
        hero_list = list(CACHE.player_profile.get('hero_stats', {}).keys())
        # DEBUG: Removed verbose hero list logging
        
        # Add basic aliases for detection
        aliases = {
            "morales": "Lt. Morales",
            "medic": "Lt. Morales",
            "etc": "E.T.C.",
            "kt": "Kael'thas",
            "ktz": "Kel'Thuzad",
            "zag": "Zagara",
            "jo": "Johanna",
            "hammer": "Sgt. Hammer",
            "bw": "Brightwing"
        }

        found_hero = None
        for hero in hero_list:
            if hero.lower() in p_low:
                found_hero = hero
                break
        
        if not found_hero:
            # Check aliases
            for alias, real_name in aliases.items():
                if alias in p_low and real_name in hero_list:
                    found_hero = real_name
                    break
        
        if found_hero:
            detected_hero = found_hero
    
    # FAST-PATH: Return instant greeting without loading data
    if is_greeting and not detected_map:
        import random
        greetings = [
            "Ready for battle, Commander. What map are we analyzing?",
            "Cerebrate online. Awaiting tactical directives.",
            "War Room systems active. How can I assist?",
            "Standing by, Commander. Request your next objective.",
            "Tactical intelligence ready. What's the mission?"
        ]
        return random.choice(greetings)
    
    # CACHE CHECK: The ResponseCache already handles simple queries via the chat() route shortcut.
    # This block is preserved only for non-simple draft queries that might still hit the cache.
    
    # CACHE CHECK: Return instant response for cached queries
    if is_draft_query and not is_forensic_audit and not image_data:
        # Lazy cache warming on first draft query
        if not RESPONSE_CACHE.warmed and len(RESPONSE_CACHE.cache) == 0:
            ColoredLogger.info("Warming cache on first query...", "CACHE")
            RESPONSE_CACHE.warm_cache()
            RESPONSE_CACHE.warmed = True
        
        cached_response = RESPONSE_CACHE.get(prompt)
        if cached_response:
            ColoredLogger.info(f"Cache HIT: {prompt[:50]}", "CACHE")
            return cached_response

    if no_numbers_mode:
        system_context = """### 🧠 CEREBRATE TACTICAL INTELLIGENCE PROTOCOL
Persona: You are the Cerebrate Analyzer, a high-fidelity tactical layer.
Tone: Authoritative, clinical, data-centric. No fluff. 
Directives:
- Address the Commander only when strictly necessary.
- Focus on high-level strategic guidance without numerical data overload.
- DO NOT use the word 'Theatre'. Use 'Map' or 'Combat Zone'.
- Provide exactly 2 tactical options.

Format:
[Map Name]
[Hero Name] - [Tactical Status] Strategic Insight: [Commander's Verdict: 1 powerful sentence on WHY this hero wins on THIS MAP] [Tactical Pivot: Mention map-specific lane flexibility]
"""
    
    else:
        system_context = f"""### 🧠 CEREBRATE TACTICAL INTELLIGENCE PROTOCOL
Persona: You are the Cerebrate Analyzer, an authoritative tactical intelligence layer.
Branding: Deliver insights via the **Neural Link** or **Nexus Intelligence** matrix.
Tone: AUTHORITATIVE, CLINICAL, DATA-CENTRIC. Zero fluff.

TACTICAL JARGON (MANDATORY USE):
- **Theoretical Value Delta**: The projected opportunity cost of a decision.
- **Positional Forensics**: Analyzing distance (dist), isolation, and team formation.
- **Macro Anchor**: A hero or player who stabilizes lane states and XP progression.
- **Unified Throughput**: Aggregated healing and sustain metrics.
- **Capital Loss**: High-value resource loss (e.g., Gems/Coins on death).

CORE DIRECTIVES:
1. **WIN RATE MANDATORY**: EVERY hero recommendation MUST include a win rate in the format: `- [XX.X]% WR [[Source]]` where Source is [Verified], [Lifetime], [S3], [Meta], or [No Data]. If no player data exists, use Global Meta win rate from context or explicitly state [No Data]. NEVER omit win rates.
2. **GRANULAR EXCELLENCE**: Every insight must include technical weights: Timestamps (MM:SS), Objective counts (e.g. 40 guardians), or Mechanical triggers (e.g. 3:00+ cooldowns).
3. **STRICT CONTEXT**: Cite all sources as [Verified], [S3], [Lifetime], or [Meta].
4. **ROSTER ENFORCEMENT**: ONLY recommend heroes in the provided roster data.
"""

        # Check for match analysis mode
        is_match_analysis = context and context.get('match_analysis_mode', False)
        
        if is_match_analysis:
            # MATCH ANALYSIS MODE - Detailed analytical breakdowns
            system_context += """
### MODE: MATCH ANALYSIS (Detailed Breakdown)
When the user asks about a match (e.g., "crushed em", "lost that match", "how did I do"), provide a COMPREHENSIVE analytical breakdown:

**REQUIRED FORMAT:**
## [Hero Name] [Win/Loss] — [Map Name]

**Verdict:** [Brief verdict from analysis if available]

**What went well:**
- [Specific stat/metric with context and numbers]
- [Strategic insight explaining why it worked]
- [Tactical highlight with impact]

**What went wrong:** (if loss)
- [Specific issue with context and how it contributed to loss]
- [Tactical mistake with timestamp if available]
- [Strategic misplay if applicable]

**The strategy:** [Explain the overall approach and why it worked/failed, referencing the match analysis summary]

**Stats:** [Key stats breakdown: K/D/A, damage, XP, Pure Soak, etc. - use actual numbers from match data]

**Takeaway:** [Actionable insight for future games - what to do differently or what worked well]

**CRITICAL REQUIREMENTS:**
- Always include specific numbers (K/D/A, damage, XP, win rates, percentages)
- Reference the match analysis data provided in the user's message
- Provide strategic context (why decisions worked/failed)
- Include tactical insights (what to do differently)
- Give clear, actionable takeaways
- Use the match analysis verdict, summary, and key insights when available
- Format numbers with commas for readability (e.g., "33,090 Hero Damage")
"""

        if is_forensic_audit:
            # FORENSIC AUDIT MODE - Narrative but data-heavy
            system_context += """
### MODE: FORENSIC AUDIT (Performance Review)
Format: Deliver a clinical, data-driven narrative of the identified trend or streak.
1. **Sequence Summary**: Identify the streak/trend clearly.
2. **Root Cause Analysis**: Use 'Theoretical Value Delta' or 'Positional Forensics' to explain failures/successes.
3. **Draft Correlation**: Relate the results to map-specific data or hero choices.
4. **Correction Logic**: Provide exactly 1-2 remediation steps.
5. **MATCH ATTRIBUTION**: When citing specific match statistics, ALWAYS include the exact map name. Format: "from the [Hero] game on [Map Name]" or "Positional Forensics from [Hero] on [Map Name] indicates...". NEVER attribute stats to the wrong map - verify the map name matches the match data you're referencing.

CRITICAL: DO NOT include "TARGETED BANS" or "MAP RECOMMENDATIONS" in this mode. These are for DEPLOYMENT mode only.
NO introductory fluff. NO friendly banter. Just technical forensics.
"""
        else:
            # DEPLOYMENT MODE - Drafting Format
            system_context += """
### MODE: DEPLOYMENT (Draft Recommendations)
STRICT RESPONSE FORMAT:
## [Map Name]
[Map Description/Directives]

🚫 **TARGETED BANS:** [Extract from BAN DOCTRINE for this Map - List Top 3]

**[Hero Name]** ([Role]) - [XX.X]% WR [[Source]]
_[Spec Name (Trigger)]_  
Strategic Insight: [Analytical sentence using Tactical Jargon].  
`[T1234567,HeroName]` (Replace with actual talent code from context - use format [T1234567,HeroName] where numbers are talent tier selections)

RULES:
- **WIN RATE FORMAT**: MUST be `- [XX.X]% WR [[Source]]` (e.g., `- 56.7% WR [[Lifetime]]` or `- 48.2% WR [[S3]]`). If no data exists, use `- [Meta WR]% WR [[Meta]]` or `- [No Data] WR [[No Data]]`.
- **MAP CONTEXT**: Include map-specific win rates when available: `(Best: MapA [XX%], MapB [YY%] | Avoid: MapC [ZZ%])` after the main WR.
- Separate heroes with blank lines.
- NO introductory fluff.
- NEXUS CONSTRAINT: Maps are random. NEVER advise 'prioritizing' or 'picking' a specific map.
- BANS: You MUST consult the 'BAN DOCTRINE' context. If the map matches a protocol, use it.

**ALTERNATIVE FORMAT (For comprehensive draft advice):**
When user asks "what should I ban/pick" or "what if I have to play [Role]", use the structured format from DRAFT_RECOMMENDATION_PROTOCOL.md:
- Include Priority Bans with Why/Impact/Counter for each
- Provide Role-Specific Recommendations for ALL roles (Tank, Assassin, Bruiser, Healer)
- Show Draft Priority order
- Include Map-Specific Notes
"""

        system_context += """
GLOBAL RULES:
- **WIN RATE ENFORCEMENT**: Every hero mentioned MUST have a win rate. Check context for: (1) Player's map-specific WR, (2) Player's lifetime/S3 WR, (3) Global Meta WR. Format: `- [XX.X]% WR [[Source]]`. If truly no data exists, use `- [No Data] WR [[No Data]]`. NEVER omit win rates - they are MANDATORY.
- **CONTEXT DATA USAGE**: The context includes hero recommendations with win rates. ALWAYS use these exact win rates in your response. Do not invent or estimate win rates.
- STATISTICAL INTEGRITY: If you cite a percentage (WR/Delta), it MUST exist in the provided Context Data. NEVER extrapolate or invent 'Theoretical Deltas' not present in the data.
- DATA INTEGRITY: A 'Streak' MUST be 3+ consecutive games of the SAME result.
- If analyzing a streak, perform a clinical audit of the last 15 games using Theoretical Value Delta logic.
- **SOCIAL INTELLIGENCE**: When social intelligence data is provided, include specific player names and their win rates in your response. Format: "Enemy [Player Name]: [X.X]% WR against ([N] games) - THREAT" or "Teammate [Player Name]: [X.X]% WR together ([N] games) - ANCHOR"."""

    # --- INJECT BRAIN PROTOCOL (The Constitution) ---
    is_complex_audit = is_forensic_audit or any(k in p_low for k in ["audit", "report", "comprehensive", "history", "trend"])
    is_social_intel = any(k in p_low for k in ["social intel", "social intelligence", "prediction", "player history"])
    
    if CACHE.brain_protocol:
        system_context = CACHE.brain_protocol + "\n\n" + system_context
        # Enforce basic rules even if not complex
        system_context += "\n1. Map Context is MANDATORY - Show top 2 best maps + worst map for EVERY hero.\n"
        system_context += "2. Prioritize Verified Data over any other source.\n"
        system_context += "3. Use clinical, data-backed terminology exclusively.\n"
        system_context += "4. DATA INTEGRITY: Do not hallucinate streaks. Report precisely what is in the Combat Log.\n"
    
    # Inject Cerebrate Template for Social Intel requests
    if is_social_intel and CACHE.cerebrate_template:
        system_context += "\n\n" + CACHE.cerebrate_template + "\n"
        system_context += "IMPORTANT: IGNORE all other formatting rules. USE THE CEREBRATE RESPONSE TEMPLATE ABOVE.\n"

    # Inject Draft Recommendation Protocol for draft queries
    is_draft_query = any(k in p_low for k in ["ban", "pick", "draft", "recommend", "what should i", "what if i"])
    if CACHE.draft_protocol and is_draft_query:
        system_context += "\n\n=== DRAFT RECOMMENDATION PROTOCOL ===\n"
        system_context += CACHE.draft_protocol + "\n"
        system_context += "CRITICAL: When providing draft recommendations, follow the DRAFT_RECOMMENDATION_PROTOCOL structure exactly.\n"

    # Only inject the full manual for complex deep-dives (if not social intel)
    if CACHE.granular_training and is_complex_audit and not is_social_intel:
        system_context += "\n\n=== GRANULAR EXCELLENCE TRAINING (COMPLEX AUDIT MODE) ===\n"
        system_context += CACHE.granular_training + "\n"
    
    # --- TARGETED CONTEXT BUILDING (Cerebrate Precision) ---
    context_str = ""
    start_time_context = time.time()
    profile = CACHE.player_profile
    
    # 0. CORE PLAYER ASSETS (Truth Anchors)
    if profile:
        audit = profile.get('storm_league_audit', {})
        strong = audit.get('strong_heroes', [])
        if strong:
            context_str += "=== TOP PERFORMANCE ASSETS (TRUSTED PICKS) ===\n"
            for h in strong[:3]:
                context_str += f"- {h['hero']}: {h['lifetime_wr']}% Lifetime WR ({h['lifetime_games']}g) | Role: {h['role']}\n"
    

    # 0.5 CURRENT UI CONTEXT (Awareness of what User is looking at)
    if context:
        context_str += "\n=== CURRENT UI CONTEXT ===\n"
        view_mode = context.get('viewMode', 'Dashboard')
        context_str += f"ACTIVE VIEW: {view_mode}\n"
        
        if context.get('selectedHero'):
            context_str += f"SELECTED HERO: {context['selectedHero']}\n"
        if context.get('selectedMatch'):
            m = context['selectedMatch']
            context_str += f"FOCUSED MATCH: {m.get('hero')} on {m.get('map')} ({m.get('result')})\n"
        if context.get('isHeroDetail'):
            context_str += "VIEW STATUS: High-Resolution Hero Detail Active\n"

    # 1. VERIFIED DATA (Directives/Rules) - Only inject if asking about rules/meta
    is_meta_query = any(k in p_low for k in ["rule", "protocol", "meta", "directive", "instruction", "how to", "guideline"])
    if CACHE.verified_data and (is_meta_query or is_complex_audit):
        # TRUNCATE Project Memory to save tokens
        ver_data_short = (CACHE.verified_data[:2000] + "...") if len(CACHE.verified_data) > 2000 else CACHE.verified_data
        context_str += f"\n=== VERIFIED PROJECT DATA (Directives) ===\n{ver_data_short}\n"
    
    # 1.5. HERO BUILD DATA (If build query detected)
    if detected_hero and profile:
        talent_builds = profile.get('talent_builds', {}).get(detected_hero, {})
        hero_stats = profile.get('hero_stats', {}).get(detected_hero, {})
        
        if talent_builds or hero_stats:
            context_str += f"\n=== {detected_hero.upper()} BUILD INTELLIGENCE ===\n"
            
            # Overall stats
            vl = hero_stats.get('verified_lifetime', {})
            vs = hero_stats.get('verified_season_2025_3', {})
            
            if vl or vs:
                context_str += "STATS (In-Game Verified):\n"
                if vl:
                    context_str += f"- LIFETIME: {vl.get('wr', 0)}% WR ({vl.get('games', 0)} games), Level {vl.get('level', 'Unknown')}\n"
                if vs:
                    context_str += f"- SEASON 3: {vs.get('wr', 0)}% WR ({vs.get('games', 0)} games)\n"
            
            # External/Parsed Intelligence (Heroes Profile)
            ext = hero_stats.get('external_intelligence', {})
            ext_maps = ext.get('map_stats', [])
            ext_builds = ext.get('talent_builds', [])

            if ext_maps:
                context_str += "\nEXTERNAL INTELLIGENCE (Heroes Profile Maps):\n"
                for m_stats in sorted(ext_maps, key=lambda x: x.get('wr', 0), reverse=True)[:8]:
                     context_str += f"- {m_stats.get('map')}: {m_stats.get('wr', 0)}% WR ({m_stats.get('games', 0)} games)\n"
            
            if ext_builds:
                 context_str += "\nEXTERNAL INTELLIGENCE (Heroes Profile Builds):\n"
                 for i, b in enumerate(ext_builds[:5], 1):
                     context_str += f"- Build {i}: {b.get('build')} | {b.get('wr', 0)}% WR ({b.get('games', 0)} games)\n"
            
            # Map-specific performance (From DB)
            db_map_stats = DB.get_hero_map_stats(detected_hero)
            if db_map_stats:
                context_str += "\nREPLAY-BASED MAP PERFORMANCE (Local):\n"
                sorted_maps = sorted(db_map_stats, key=lambda x: x.get('win_rate', 0), reverse=True)
                for stats in sorted_maps[:5]:
                    context_str += f"- {stats.get('map')}: {stats.get('win_rate', 0):.1f}% WR ({stats.get('games_played', 0)} games)\n"
            
            # Replay-based

            # Talent builds (From DB)
            db_builds = DB.get_top_builds(detected_hero, limit=5)
            if db_builds:
                context_str += f"\nREPLAY-BASED BUILD PERFORMANCE (Local):\n"
                for i, b in enumerate(db_builds, 1):
                    build_clean = b['build_code'].replace('-', '')
                    context_str += f"{i}. {b['win_rate']}% WR ({b['games']}g) - Build: {build_clean}\n"
                    context_str += f"   Code: `[T{build_clean},{detected_hero}]`\n"
            else:
                # Provide default build if no data available
                DEFAULT_BUILDS_FALLBACK = {
                    "Jaina": "T2221222", "Li-Ming": "T2221222", "Kael'thas": "T2221222", 
                    "Tychus": "T1231214", "Greymane": "T2221222", "Raynor": "T1132112",
                    "Valla": "T2321221", "Falstad": "T2221222", "Sylvanas": "T1111111"
                }
                default_code = DEFAULT_BUILDS_FALLBACK.get(detected_hero, "T1111111")
                context_str += f"No talent build data available for {detected_hero}.\n"
                context_str += f"Default build: `[T{default_code},{detected_hero}]`\n"

    # 1.6. RECENT MATCH HISTORY (From DB)
    if is_streak_query:
        try:
            # Reduce limit to 10 to save tokens and keep focus tight
            subset = DB.get_recent_matches(limit=10)
            
            context_str += f"\n=== RECENT COMBAT LOG (Last 10 Games) ===\n"
            for m in subset:
                date_str = m.get('date', 'Unknown')[:10]
                result = m.get('result', 'Unknown')
                hero = m.get('hero', 'Unknown')
                map_n = m.get('map', 'Unknown')
                verdict = m.get('analysis_verdict', 'No Verdict')
                summary = m.get('analysis_summary', 'No summary available.')
                mistake = m.get('critical_mistake', 'None recorded.')
                
                # Truncate summary to keep context lean and prevent quota hits
                summary_short = (summary[:300] + '...') if len(summary) > 300 else summary
                
                context_str += f"- {date_str} | {result} | {hero} | {map_n}\n"
                context_str += f"  Verdict: {verdict}\n"
                context_str += f"  Summary: {summary_short}\n"
                context_str += f"  Mistake: {mistake}\n"
            
            # Enhanced Streak Detection (Context Aware)
            if subset:
                # 1. Determine what result the user is interested in
                interest = None
                p_low = prompt.lower()
                if "loss" in p_low: interest = "LOSS"
                elif "win" in p_low: interest = "WIN"
                
                streak_type = subset[0].get('result', 'LOSS')
                target_idx = 0
                
                # If user specified a type, find the most recent game of that type to anchor the streak
                if interest:
                    for i, m in enumerate(subset):
                        if m.get('result') == interest:
                            streak_type = interest
                            target_idx = i
                            break
                            
                # Calculate consecutive count starting from target_idx
                streak_count = 0
                for i in range(target_idx, len(subset)):
                    if subset[i].get('result') == streak_type:
                        streak_count += 1
                    else:
                        break
                
                # Identify maps involved specifically in this streak
                streak_maps = []
                for i in range(target_idx, target_idx + streak_count):
                    if i < len(subset):
                        streak_maps.append(subset[i].get('map', 'Unknown Map'))
                
                # Ensure streak_maps is a list of strings
                maps_involved_list = list(dict.fromkeys(streak_maps))
                valid_maps = [str(m) for m in maps_involved_list if m is not None]
                maps_involved = ", ".join(valid_maps)
                
                if streak_count >= 3:
                    context_str += f"\n[TACTICAL THREAD: {streak_count}-Game {streak_type} sequence identified across {maps_involved}. Audit this as a {streak_type} sequence.]\n"
                else:
                    context_str += f"\n[TACTICAL THREAD: Mixed Tactical Outcomes detected ({streak_count} games of {streak_type}). Perform a clinical audit of individual recent matches to identify performance variance.]\n"
                
                context_str += f"INSTRUCTION: Perform a forensic audit of the {streak_type if interest else 'mixed'} sequence. "
                if streak_type == "LOSS":
                    context_str += "Analyze WHY these losses occurred (e.g. hero choice vs map, build failures). "
                context_str += "CRITICAL: Do not hallucinate numbers. Only use win rates provided in the context. Maps are randomly selected; do not advise 'prioritizing' a map, only advise for the context provided. "
                context_str += "**MATCH ATTRIBUTION RULE**: When citing specific match statistics (Hero Damage, deaths, etc.), you MUST include the exact map name where those stats occurred. Format: 'from the [Hero] game on [Map Name]' or 'Positional Forensics from [Hero] on [Map Name] indicates...'. NEVER attribute stats to the wrong map.\n"
        except Exception as e:
            context_str += f"\nError loading match history for streak analysis: {e}\n"

    # 2. DRAFT/STRATEGY INTEL (Targeted Hero Data)
    if is_draft_query and profile:
        audit = profile.get('storm_league_audit', {})
        hero_names = set(profile.get('hero_map_stats', {}).keys())
        clean_p = p_low.replace(' ', '').replace("'", "")
        
        # Load Ban Recommendations
        ban_context = ""
        try:
             with open('.agent/brain/BAN_RECOMMENDATIONS.md', 'r') as f:
                 ban_context = f"\n=== BAN DOCTRINE ===\n{f.read()}\n"
        except:
             pass
        
        # Extract map name from query (duplicate detection for draft queries)
        map_keywords_draft = {
            'infernalshrines': 'Infernal Shrines',
            'battlefieldofeternity': 'Battlefield of Eternity',
            'boe': 'Battlefield of Eternity',
            'dragonshire': 'Dragon Shire',
            'blackheartsbay': "Blackheart's Bay",
            'blackhearts': "Blackheart's Bay",
            'skytemple': 'Sky Temple',
            'tombofthespiderqueen': 'Tomb of the Spider Queen',
            'tomb': 'Tomb of the Spider Queen',
            'alteracpass': 'Alterac Pass',
            'alterac': 'Alterac Pass',
            'volskayafoundry': 'Volskaya Foundry',
            'volskaya': 'Volskaya Foundry',
            'gardenofterror': 'Garden of Terror',
            'garden': 'Garden of Terror',
            'cursedhallow': 'Cursed Hollow',
            'cursed': 'Cursed Hollow',
            'towersofdoom': 'Towers of Doom',
            'towers': 'Towers of Doom',
            'braxisholdout': 'Braxis Holdout',
            'braxis': 'Braxis Holdout',
            'hanamuratemple': 'Hanamura Temple',
            'hanamura': 'Hanamura Temple',
            'warheadjunction': 'Warhead Junction',
            'warhead': 'Warhead Junction'
        }
        
        detected_map = None
        for keyword, map_name in map_keywords.items():
            if keyword in clean_p:
                detected_map = map_name
                break
        
        if detected_map:
            context_str += f"\nDETECTED THEATRE: {detected_map}\n"
            # Only show bans if not filtering by role
            if not detected_role:
                context_str += ban_context # Inject Ban Doctrine
            
        # Find heroes mentioned in query
        mentioned_heroes = [h for h in hero_names if h.lower().replace(' ', '').replace("'", "") in clean_p]
        
        
        # If map is detected but no heroes mentioned, get best heroes for that map
        if detected_map and not mentioned_heroes:
            # Load excluded heroes specifically for this context building
            hero_prefs = profile.get('hero_preferences', {})
            excluded_heroes = set()
            excluded_heroes.update(hero_prefs.get('dislike', []))
            excluded_heroes.update(hero_prefs.get('rarely_play', []))

            context_str += f"\n=== TARGETED MISSION DATA FOR {detected_map.upper()} ===\n"
            m_data = CACHE.mission_cache.get(detected_map, {})
            if m_data:
                context_str += f"DESCRIPTION: {m_data.get('desc')}\n"
                # Only show bans if not filtering by role
                if not detected_role:
                    bans = m_data.get('bans', [])
                    ban_list = []
                    for b in bans:
                        if isinstance(b, dict):
                            ban_list.append(f"{b['hero']} ({b.get('reason', 'Map Threat')})")
                        else:
                            ban_list.append(str(b))
                    if ban_list:
                        context_str += f"3-BAN STANDARDS: {', '.join(ban_list)}\n"
                context_str += f"TACTICAL RECOMMENDATIONS:\n"
                for h in m_data.get('heroes', []):
                    # Filter by role if detected
                    if detected_role and h.get('role') != detected_role:
                        continue
                    # Filter by exclusion list (RESPECT PREFERENCES)
                    if h.get('hero') in excluded_heroes:
                        continue
                    
                    context_str += f"- {h['hero']} ({h['role']}): {h['wr']}% WR {h['source']}. Trigger: {h['trigger']}. Insight: {h['insight']}\n"
            
            # Continue with role-based backups...
            context_str += f"\n=== ROLE-BASED HISTORICAL ASSETS ===\n"
            
            # Load player's owned heroes (from KV store)
            owned_heroes = set()
            hero_levels = {}
            try:
                roster_data = DB.get_kv('hero_roster_levels') or {}
                owned_heroes = set(roster_data.get('heroes', {}).keys())
                hero_levels = roster_data.get('heroes', {})
            except:
                pass
            
            # Load banned heroes from config (from KV store)
            banned_heroes = set()
            try:
                config = DB.get_kv('cerebrate_config') or {}
                banned_heroes = set(config.get('roster_constraints', {}).get('global_bans', []))
            except:
                pass
            
            # Build role-based recommendations (top 2 per role)
            # If role is detected, only build recommendations for that role
            if detected_role:
                role_recommendations = {detected_role: []}
            else:
                role_recommendations = {
                    'Tank': [],
                    'Healer': [],
                    'Ranged Assassin': [],
                    'Bruiser': []
                }
            
            # Get hero role mapping
            hero_to_role = {}
            for role, heroes in CACHE.hero_roles.items():
                for hero in heroes:
                    hero_to_role[hero] = role
            
            # 1. Find best heroes per role from player's map data (top 3 per role)
            role_candidates = {role: [] for role in role_recommendations}
            
            # First, check profile hero_map_stats
            for hero, stats in profile.get('hero_map_stats', {}).items():
                if hero in banned_heroes:
                    continue
                    
                role = hero_to_role.get(hero)
                if not role or role not in role_recommendations:
                    continue
                
                # Check season_2025_3 and lifetime for this map
                for map_data in stats.get('season_2025_3', []) + stats.get('lifetime', []):
                    if map_data['game_map'] == detected_map:
                        wr = float(map_data['win_rate'])
                        games = map_data.get('games_played', map_data.get('games', 0))  # Handle both field names
                        # Filter: minimum 3 games AND 45%+ WR (don't recommend losing builds)
                        if games >= 3 and wr >= 45.0:
                            role_candidates[role].append({
                                'hero': hero,
                                'wr': wr,
                                'games': games,
                                'source': map_data.get('source', 'Historical'),
                                'has_player_data': True
                            })
                        break
            
            # 1.5. Supplement with direct database queries for heroes not in profile
            # This catches heroes with DB data but missing from profile
            try:
                all_heroes_in_db = set()
                with DB._get_connection() as conn:
                    rows = conn.execute('SELECT DISTINCT hero FROM matches WHERE map = ?', (detected_map,)).fetchall()
                    all_heroes_in_db = {row['hero'] for row in rows if row['hero']}
                
                for hero in all_heroes_in_db:
                    if hero in banned_heroes:
                        continue
                    if hero not in owned_heroes:
                        continue
                    
                    role = hero_to_role.get(hero)
                    if not role or role not in role_recommendations:
                        continue
                    
                    # Check if already in candidates
                    already_added = any(c['hero'] == hero for c in role_candidates[role])
                    if already_added:
                        continue
                    
                    # Query database for this hero on this map
                    db_map_stats = DB.get_hero_map_stats(hero)
                    for stat in db_map_stats:
                        if stat['map'] == detected_map:
                            wr = stat['win_rate']
                            games = stat['games_played']
                            if games >= 1:  # Include all data
                                role_candidates[role].append({
                                    'hero': hero,
                                    'wr': wr,
                                    'games': games,
                                    'source': 'Replay Archive',
                                    'has_player_data': True
                                })
                            break
            except Exception as e:
                pass  # Silent fail - profile data is primary
            
            
            # Sort each role by WR and take top 3 (increased to include comfort picks)
            for role in role_recommendations:
                role_candidates[role].sort(key=lambda x: x['wr'], reverse=True)
                role_recommendations[role] = role_candidates[role][:3]  # Top 3 per role (was 2)
            
            # Get excluded heroes
            hero_prefs = profile.get('hero_preferences', {})
            excluded_heroes = set()
            excluded_heroes.update(hero_prefs.get('dislike', []))
            excluded_heroes.update(hero_prefs.get('rarely_play', []))
            
            # 2. Fill missing roles ONLY with heroes that have stats (no meta fallback without stats)
            # DYNAMIC META LOOKUP (No Hardcoded Lists)
            map_meta = {} # We will now query the DB/Cache dynamically
            
            # Helper to get top global winrate heroes for this map (if we had map-specific global data)
            # Since we only have global hero stats, we can use that as a proxy for "Meta" but filtered by Role
            
            # Filter global meta by role to create dynamic suggestion lists
            global_meta_by_role = {}
            if CACHE.global_meta:
                for h_meta in CACHE.global_meta:
                    h_name = h_meta.get('hero') or h_meta.get('name')
                    h_role = hero_to_role.get(h_name) # Use our role mapping
                    if h_role:
                        if h_role not in global_meta_by_role:
                            global_meta_by_role[h_role] = []
                        global_meta_by_role[h_role].append(h_name)
            # Assign dynamic meta to map_meta for compatibility with below logic
            map_meta = global_meta_by_role
            # Get hero stats for checking if meta heroes have any stats
            hero_stats_all = profile.get('hero_stats', {})
            
            for role in role_recommendations:
                current_count = len(role_recommendations[role])
                # Check if we already have heroes with stats for this role
                has_stats = any(r.get('has_player_data', False) and r.get('games', 0) > 0 for r in role_recommendations[role])
                
                if current_count < 2:
                    # Get meta picks for this role
                    meta_heroes = map_meta.get(role, [])
                    for meta_hero in meta_heroes:
                        if len(role_recommendations[role]) >= 2:
                            break
                        # Skip excluded heroes
                        if meta_hero in excluded_heroes:
                            continue
                        # Only recommend if owned and not banned
                        if meta_hero in owned_heroes and meta_hero not in banned_heroes:
                            # Check if already recommended
                            existing_heroes = [r['hero'] for r in role_recommendations[role]]
                            if meta_hero not in existing_heroes:
                                # Check if we have stats for this hero (even if not map-specific)
                                hero_data = hero_stats_all.get(meta_hero, {})
                                lifetime = hero_data.get('verified_lifetime', {})
                                season = hero_data.get('verified_season_2025_3', {})
                                total_games = lifetime.get('games', 0) + season.get('games', 0)
                                
                                # Only add meta hero if:
                                # 1. We have NO heroes with stats for this role, OR
                                # 2. This meta hero has stats (even if not map-specific)
                                if has_stats and total_games == 0:
                                    continue  # Skip - user wants stats-based recommendations
                                
                                if total_games > 0:
                                    # Use overall stats
                                    wr = lifetime.get('win_rate', lifetime.get('wr', 50)) or season.get('win_rate', season.get('wr', 50)) or 50
                                    # Only recommend if WR is decent (45%+) - don't recommend heroes you play poorly
                                    if float(wr) >= 45.0:
                                        hero_level = hero_levels.get(meta_hero, 0)
                                        role_recommendations[role].append({
                                            'hero': meta_hero,
                                            'wr': float(wr),
                                            'games': total_games,
                                            'level': hero_level,
                                            'source': 'Your Stats (All Maps)',
                                            'has_player_data': True
                                })
                                # Don't add meta heroes with 0 games or low WR - user doesn't trust recommendations without stats
            
            # 3. Format recommendations for AI context (sorted by WR, highest first)
            sorted_recs = []
            for role, recs in role_recommendations.items():
                for rec in recs:
                    # Assign sort priority: player data gets WR, meta gets -1
                    sort_key = rec['wr'] if rec['has_player_data'] else -1
                    sorted_recs.append((sort_key, role, rec))
            
            sorted_recs.sort(key=lambda x: x[0], reverse=True)
            
            for _, role, rec in sorted_recs:
                if rec['has_player_data']:
                    status = "Dominating" if rec['wr'] > 58 else "Strong" if rec['wr'] > 53 else "Consistent" if rec['wr'] > 48 else "Developing"
                    source_str = str(rec.get('source', 'Record') or 'Record')
                    source_tag = '[Lifetime]' if 'lifetime' in source_str.lower() else '[S3]' if 'season' in source_str.lower() else '[Verified]' if 'verified' in source_str.lower() else '[Historical]'
                    games_count = rec.get('games', 0) or 0
                    context_str += f"[{rec['hero']} ({role})] @ {detected_map}: {status} - {rec['wr']:.1f}% WR {source_tag} ({games_count} games)\n"
                else:
                    # Try to get Global Meta WR for this hero
                    meta_wr = None
                    for hero_meta in CACHE.global_meta:
                        if hero_meta.get('hero') == rec['hero'] or hero_meta.get('name') == rec['hero']:
                            meta_wr = hero_meta.get('win_rate', 0)
                            break
                    
                    level = rec.get('level', 0)
                    if meta_wr:
                        context_str += f"[{rec['hero']} ({role})] @ {detected_map}: No Player Data (Level {level}) - {meta_wr:.1f}% WR [[Meta]]\n"
                    else:
                        context_str += f"[{rec['hero']} ({role})] @ {detected_map}: No Data (Level {level}) - [No Data] WR [[No Data]]\n"
        
        # If specific heroes mentioned, load their data
        elif mentioned_heroes:
            context_str += "\n=== TARGETED DRAFT INTEL ===\n"
            for hero in mentioned_heroes:
                m_stats = profile.get('hero_map_stats', {}).get(hero)
                wr_found = False
                if m_stats:
                    if detected_map:
                        # Find specific map data
                        target = next((m for m in (m_stats.get('season_2025_3', []) + m_stats.get('lifetime', [])) 
                                      if m['game_map'] == detected_map), None)
                    else:
                        # Find any map mentioned in query
                        target = next((m for m in (m_stats.get('season_2025_3', []) + m_stats.get('lifetime', [])) 
                                      if m['game_map'].lower().replace(' ', '').replace("'", "") in clean_p), None)
                    
                    if target:
                        wr = float(target['win_rate'])
                        status = "Dominating" if wr > 58 else "Strong" if wr > 53 else "Consistent" if wr > 48 else "Underperforming"
                        source = target.get('source', 'Historical')
                        source_tag = '[Lifetime]' if 'lifetime' in str(target.get('source', '')).lower() else '[S3]' if 'season' in str(target.get('source', '')).lower() else '[Verified]'
                        context_str += f"[{hero} @ {target['game_map']}]: {status} ({wr:.1f}% WR {source_tag}) (Source: {source})\n"
                        wr_found = True
                
                # Fallback to Global Meta if no player data
                # BUT FIRST: Filter out heroes you don't own (Constraint Enforcement)
                # Load ownership data if not already present
                if 'owned_heroes' not in locals():
                     roster_data = DB.get_kv('hero_roster_levels') or {}
                     owned_heroes = roster_data.get('heroes', {})

                if not wr_found:
                    # Check ownership before suggesting meta
                    is_owned = hero in owned_heroes
                    
                    if is_owned:
                        meta_wr = None
                        for hero_meta in CACHE.global_meta:
                            if hero_meta.get('hero') == hero or hero_meta.get('name') == hero:
                                meta_wr = hero_meta.get('win_rate', 0)
                                break
                        
                        if meta_wr:
                            context_str += f"[{hero}]: No Player Data | Global Meta: {meta_wr:.1f}% WR [[Meta]]\n"
                        else:
                            context_str += f"[{hero}]: No Data Available [[No Data]]\n"
                    else:
                        # Skip showing unowned heroes in the "Targeted" section to reduce noise
                        pass
        
        # Fallback: if no map detected and no heroes mentioned, use audit
        elif not detected_map and not mentioned_heroes:
            # MOVED UP - audit = profile.get('storm_league_audit', {})
            context_str += "\n=== TOP PERFORMERS (OVERALL) ===\n"
            for h in audit.get('strong_heroes', [])[:3]:
                context_str += f"[{h['hero']}]: {h.get('status', 'Strong')} ({h.get('win_rate', 'N/A')}% WR)\n"

    # 3. POST-MATCH ANALYSIS
    if is_post_match:
        matches = context.get('recentMatches', []) if context else []
        if matches and matches[0].get('analysis'):
            an = matches[0]['analysis']
            context_str += f"\n=== LAST MATCH ANALYSIS ===\nVerdict: {an.get('verdict')}\nSummary: {an.get('summary')}\n"

        context_str += f"\n=== AUDIT SYNOPSIS ===\n"
        context_str += f"STRONG: {', '.join([str(h.get('hero', 'Unknown')) for h in audit.get('strong_heroes', [])[:4]])}\n"
        context_str += f"SLUMPING: {', '.join([str(h.get('hero', 'Unknown')) for h in audit.get('slumping_heroes', [])[:3]])}\n"
        context_str += f"MAP PREFS: {profile.get('map_preferences', {}).get('strong', [])[:3]}\n"
    
    # 4.5 HERO ROSTER (Ownership Constraint) - from KV store
    try:
        roster_data = DB.get_kv('hero_roster_levels') or {}
        owned_heroes = roster_data.get('heroes', {})
        if owned_heroes:
            context_str += f"\n=== COMMANDER'S HERO ROSTER ===\n"
            context_str += f"OWNED HEROES ({len(owned_heroes)}): {', '.join([str(k) for k in sorted(owned_heroes.keys())])}\n"
            context_str += "CONSTRAINT: ONLY recommend heroes from this list. NEVER suggest unowned heroes.\n"
    except Exception as e:
        pass
    
    # 5. SOCIAL INTELLIGENCE (Player Network Analysis)
    if CACHE.player_interactions and (is_draft_query or 'social' in p_low or 'player' in p_low or 'network' in p_low):
        context_str += f"\n=== SOCIAL INTELLIGENCE ===\n"
        
        # Calculate network stats
        players_data = CACHE.player_interactions
        strong_allies = []
        nemeses = []
        frequent_rivals = []
        all_known_players = []
        
        for player_name, player_data in players_data.items():
            total_with = player_data.get('total_with', 0)
            total_against = player_data.get('total_against', 0)
            wins_with = player_data.get('wins_with', 0)
            wins_against = player_data.get('wins_against', 0)
            
            # Calculate win rates
            wr_with = (wins_with / total_with * 100) if total_with > 0 else 0
            wr_against = (wins_against / total_against * 100) if total_against > 0 else 0
            
            # Track all known players for context
            if total_with > 0 or total_against > 0:
                all_known_players.append({
                    'name': player_name,
                    'wr_with': wr_with,
                    'wr_against': wr_against,
                    'games_with': total_with,
                    'games_against': total_against
                })
            
            # Identify strong allies (60%+ WR, 3+ games)
            if total_with >= 3 and wr_with >= 60:
                strong_allies.append((player_name, wr_with, total_with))
            
            # Identify nemeses (<40% WR against, 3+ games)
            if total_against >= 3 and wr_against < 40:
                nemeses.append((player_name, wr_against, total_against))
            
            # Identify frequent rivals (played both with and against, 3+ each)
            if total_with >= 3 and total_against >= 3:
                frequent_rivals.append((player_name, wr_with, total_with, wr_against, total_against))
        
        # Sort and format
        strong_allies.sort(key=lambda x: x[1] * x[2], reverse=True)  # Sort by value score
        nemeses.sort(key=lambda x: x[1] * x[2])  # Lowest value score = biggest threat
        frequent_rivals.sort(key=lambda x: x[2] + x[4], reverse=True)  # Most total games
        
        # Enhanced social intelligence output
        context_str += f"NETWORK SIZE: {len(players_data)} tracked players\n\n"
        
        # Strong Allies Section
        if strong_allies:
            context_str += "🤝 STRONG ALLIES (Synergy Anchors):\n"
            for ally in strong_allies[:5]:  # Top 5 allies
                context_str += f"- {ally[0]}: {ally[1]:.1f}% WR together ({ally[2]} games) - ANCHOR\n"
            context_str += "\n"
        else:
            context_str += "🤝 STRONG ALLIES: None identified (need 3+ games, 60%+ WR)\n\n"
        
        # Nemeses Section
        if nemeses:
            context_str += "⚠️ NEMESES (Enemy Threats):\n"
            for nemesis in nemeses[:5]:  # Top 5 nemeses
                context_str += f"- {nemesis[0]}: {nemesis[1]:.1f}% WR against ({nemesis[2]} games) - THREAT\n"
            context_str += "\n"
        else:
            context_str += "⚠️ NEMESES: None identified (need 3+ games, <40% WR against)\n\n"
        
        # Frequent Rivals Section
        if frequent_rivals:
            context_str += "⚔️ FREQUENT RIVALS (Played both with and against):\n"
            for rival in frequent_rivals[:3]:  # Top 3 rivals
                context_str += f"- {rival[0]}: {rival[1]:.1f}% WR with ({rival[2]}g) | {rival[3]:.1f}% WR against ({rival[4]}g)\n"
            context_str += "\n"
        
        # All Known Players (for draft context)
        if all_known_players and ('social' in p_low or 'player' in p_low):
            context_str += "📊 ALL KNOWN PLAYERS IN NETWORK:\n"
            # Sort by total games
            all_known_players.sort(key=lambda x: x['games_with'] + x['games_against'], reverse=True)
            for p in all_known_players[:10]:  # Top 10 most frequent
                with_info = f"{p['wr_with']:.1f}% WR ({p['games_with']}g)" if p['games_with'] > 0 else "No data"
                against_info = f"{p['wr_against']:.1f}% WR ({p['games_against']}g)" if p['games_against'] > 0 else "No data"
                context_str += f"- {p['name']}: With: {with_info} | Against: {against_info}\n"
            context_str += "\n"
        
        context_str += "SOCIAL DIRECTIVE: When making recommendations:\n"
        context_str += "- If strong allies detected, suggest synergistic heroes and coordinate macro strategies\n"
        context_str += "- If nemeses detected, recommend counter-picks and defensive macro (0-death discipline)\n"
        context_str += "- If tilt targets detected (0% WR against you), suggest aggressive gank strategies\n"
        context_str += "- Always include specific player names and win rates when providing social intelligence\n"

    # --- PROMPT CONSTRUCTION ---
    if raw_mode:
        full_prompt = prompt
    else:
        full_prompt = f"{system_context}\n\n{context_str}\n\nUser: {prompt}"
    
    map_tag = f" | {ColoredLogger.CYAN}{detected_map}{ColoredLogger.RESET}" if 'detected_map' in locals() and detected_map else ""
    # Try to find detected_map in outer scope if not in locals
    if not map_tag:
        try:
            # We are inside call_gemini_api, lets see if we can get it from the prompt
            p_low = prompt.lower()
            # Reuse map detection logic briefly for logging
            maps_list = ['Shrines', 'Eternity', 'Dragon', 'Bay', 'Temple', 'Tomb', 'Alterac', 'Volskaya', 'Garden', 'Hollow', 'Doom', 'Braxis', 'Hanamura', 'Warhead']
            for m in maps_list:
                if m.lower() in p_low:
                    map_tag = f" | {ColoredLogger.CYAN}{m}{ColoredLogger.RESET}"
                    break
        except: pass
    if not silent:
        ColoredLogger.processing(f"Generating Tactical Analysis{map_tag} ({len(full_prompt)} chars)", "AI")
    
    # --- GEMINI API CALL (Vision Enabled) ---
    parts = [{"text": full_prompt}]
    if image_data:
        if isinstance(image_data, str) and image_data.startswith("data:image"):
             image_data = image_data.split(",")[1]
        parts.append({
            "inline_data": {
                "mime_type": "image/png",
                "data": image_data
            }
        })
    max_retries = 3
    base_delay = 5

    for model_name, level_name in tiers:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent'
        
        for attempt in range(max_retries):
            try:
                # Log model attempt if not silent
                if attempt == 0 and not silent:
                    ColoredLogger.processing(f"Linking to {model_name} ({level_name})...", "AI")
                
                response = requests.post(
                    f"{url}?key={GEMINI_API_KEY}",
                    json={"contents": [{"parts": parts}]},
                    timeout=120
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'candidates' in data and len(data['candidates']) > 0:
                        candidate = data['candidates'][0]
                        if 'content' in candidate and 'parts' in candidate['content']:
                            # SUCCESS: Update globals
                            LAST_ACTUAL_MODEL = model_name
                            TACTICAL_LINK_LEVEL = level_name
                            result_text = candidate['content']['parts'][0]['text']
                            
                            # Record request in quota manager
                            QUOTA.record_request(model_name)
                            
                            # DEBUG: Log raw response for audit
                            if not silent:
                                print(f"--- RAW AI RESPONSE ({model_name}) ---\n{result_text}\n----------------------------------")
                                
                            return result_text
                        else:
                            return f"AI Generation Failed. Reason: {candidate.get('finishReason', 'Unknown')}"
                    else:
                        return "Sorry, I couldn't generate a response. Please try again."
                
                elif response.status_code == 429:
                    # Quota Exceeded - Fall back quickly if it's the first attempt, or retry if it's the only tier left
                    if attempt < 1 and model_name != tiers[-1][0]:
                        next_tier = tiers[tiers.index((model_name, level_name)) + 1][0]
                        ColoredLogger.tier_shift(model_name, next_tier, "Quota Hit")
                        break # Break attempt loop to move to next tier
                    
                    wait_time = base_delay * (2 ** attempt)
                    if not silent:
                        ColoredLogger.warn(f"Quota exceeded on {model_name}. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                
                elif response.status_code == 404:
                    # Model not found in this region/env - fall back immediately
                    if model_name != tiers[-1][0]:
                        next_tier = tiers[tiers.index((model_name, level_name)) + 1][0]
                        ColoredLogger.tier_shift(model_name, next_tier, "Model Unavailable")
                    else:
                        ColoredLogger.error(f"Ultimate Tier Failure: {model_name} not available.")
                    break 
                    
                else:
                    ColoredLogger.error(f"API Error ({response.status_code}): {response.text}")
                    break # Move to next tier
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
                    continue
                break # Move to next tier
    
    return "API Error: Tactical Link Failure. All model tiers exhausted."

def enforce_map_context(ai_response, detected_map=None):
    """
    Validates that hero recommendations include map context.
    Enforces the Cerebrate Protocol's Map Context Mandate.
    
    Returns: (validated_response, has_map_context_flag)
    """
    import re
    
    # Pattern to detect hero recommendations
    # Matches: **HeroName** or **Hero Name**
    hero_pattern = r'\*\*([A-Z][a-z]+(?:\s[A-Z][a-z]+)?(?:\'[a-z]+)?)\*\*'
    heroes_mentioned = re.findall(hero_pattern, ai_response)
    
    if not heroes_mentioned or len(heroes_mentioned) == 0:
        return ai_response, True  # No heroes to validate
    
    # Check if map context exists in the response
    map_context_patterns = [
        r'Best:.*?\[.*?%\]',  # "Best: Map [XX%]"
        r'@\s+[A-Z]',         # "@ MapName"
        r'\d+%.*?on.*?[A-Z]', # "XX% on MapName"
        r'Avoid:.*?[A-Z]',    # "Avoid: MapName"
        r'Strong on:',        # "Strong on:"
        r'Weak on:',          # "Weak on:"
    ]
    
    has_map_context = any(re.search(pattern, ai_response, re.IGNORECASE) for pattern in map_context_patterns)
    
    # If map was detected in query, check if it's mentioned in response
    if detected_map and detected_map in ai_response:
        has_map_context = True
    
    if not has_map_context and len(heroes_mentioned) > 0:
        # Add warning banner for missing map context
        warning = "⚠️ **MAP CONTEXT MISSING**: These recommendations need map-specific validation. Ask: 'What maps are best for [Hero]?'\n\n"
        return warning + ai_response, False
    
    return ai_response, True


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests."""
    start_time = time.time()
    try:
        data = request.get_json()
        message = data.get('message', '')
        context = data.get('context', {})
        image_data = data.get('image') # Base64 image string
        
        if not message and not image_data:
            return jsonify({'error': 'No message or image provided'}), 400
        
        # Detect if this is a draft prediction request
        is_prediction = image_data and ("prediction" in message.lower() or message.lower().strip() == "" or message.lower() == "prediction")
        
        if image_data and not message:
            message = "prediction"  # Default to prediction for image-only requests

        # If it's a prediction with image, route to draft analysis
        if is_prediction and image_data:
            # Use analyze_image logic for draft predictions
            try:
                # Get player's known name/battletag for identification
                import os
                player_name = os.environ.get('PLAYER_NAME', 'Discerning')
                player_battletag = os.environ.get('PLAYER_BATTLE_TAG', 'Discerning#2567')
                known_aliases = [player_name, player_battletag, 'jmoncayo', 'Cerebrate']
                
                # Load player interactions for social intelligence
                # OPTIMIZATION: Load top 1200 players by frequency (covers almost all historical interactions)
                player_interactions = CACHE.player_interactions or {}
                
                # Sort by total games (with + against) descending
                sorted_interactions = sorted(
                    player_interactions.items(), 
                    key=lambda x: x[1].get('total_with', 0) + x[1].get('total_against', 0), 
                    reverse=True
                )
                
                known_players = []
                # Compress into a very tight format to fit more players in context
                for pid, data in sorted_interactions[:1200]:
                    name = data.get('name', pid)
                    w_with = data.get('wins_with', 0)
                    t_with = data.get('total_with', 0)
                    w_agst = data.get('wins_against', 0)
                    t_agst = data.get('total_against', 0)
                    
                    if t_with > 0 or t_agst > 0:
                        known_players.append(f"{name}|W:{w_with}/{t_with}|A:{w_agst}/{t_agst}")
                
                social_context = ""
                if known_players:
                    social_context = "\n\n**COMMANDER DATABASE (TOP 1200):**\n" + ", ".join(known_players)
                
                # Build player stats context
                profile = CACHE.player_profile or {}
                stats_context = ""
                if profile and profile.get('hero_stats'):
                    top_heroes = []
                    for hero, data in list(profile['hero_stats'].items())[:10]:
                        lifetime = data.get('verified_lifetime', {})
                        if lifetime:
                            wr = lifetime.get('win_rate', lifetime.get('wr', 0))
                            games = lifetime.get('games', lifetime.get('games_played', 0))
                            if games > 0:
                                top_heroes.append(f"{hero}: {wr:.1f}% WR ({games} games)")
                    if top_heroes:
                        stats_context = "\n\n**YOUR TOP PERFORMERS:**\n" + "\n".join(top_heroes)
                
                # Build draft recommendation prompt
                draft_prompt = f"""Analyze this Heroes of the Storm LOADING SCREEN screenshot. 

**PHASE 1: USER IDENTIFICATION (CRITICAL)**
1. Scan for the name "{player_name}" or "{player_battletag}".
2. Identifiably locating "{player_name}" in the OCR results determines which side is the ALLY TEAM.
3. Mark the player matching "{player_name}" as [YOU].

**PHASE 2: SOCIAL INTELLIGENCE SCAN (CROSS-REFERENCE)**
Compare EVERY visible name in the screenshot against the **KNOWN PLAYERS** list provided below.
If a name matches (e.g., "Player" or "RangeDestryR"), you MUST use their historical win/loss data in your Assessment.

**YOUR MISSION:**
You are the AI Assistant "CEREBRATE". Provide tactical analysis following this EXACT structure:

## {detected_map if detected_map else '[MAP NAME]'} // [WIN CONDITION]
*Objective: [Brief objective description]*

### 1. SOCIAL INTELLIGENCE
*   **User Identification:** [Identify {player_name} and confirm their hero and team. Highlight them as [YOU]]
*   **Combatant Scan:** [OCR EVERY name in the screenshot and list them here grouped BY TEAM. Mark {player_name} as [YOU]]
*   **Social Analysis:** [Compare names against the COMMANDER DATABASE. For any match (even partial), list their historical record with/against you.]
*   **Verdict:** [Classify combatants as Anchor, Apex Threat, or Stable Link based on their records.]

### 2. TACTICAL PREDICTION
*   **Ally Team Analysis:** [Analyze the 5 heroes on the team containing {player_name}]
*   **Enemy Team Analysis:** [Analyze the 5 heroes on the opposing team]
*   **Win Condition:** **[PRIMARY GOAL]** [Map-specific win condition for YOUR team]
*   **Risk:** **[NEURAL DESYNC RISK]** [Identify enemy heroes or player matchups that threaten your victory]

### 3. DIRECTIVE: [YOUR HERO NAME]
**Confidence: [XX]%**
*   **Verified Metric:** [Your WR on this hero]% on this map.
*   **Strategic Insight:** [Granular tactical advice for YOUR hero in this specific match]
`[T1234567,HeroName]`

**📊 DATA SOURCES:** SQLite interaction matrix + {player_name}'s Performance Ledger.

**CRITICAL PROTOCOLS:**
1. **SIDE VALIDATION:** The team with "{player_name}" is ALWAYS the ALLY TEAM. The other team is ALWAYS the ENEMY TEAM. Do not swap them.
2. **NAME MATCHING:** Cross-reference the names in the image (RichAtreides, SunDan, Tvoun, JohnTitor, etc.) against the database provided.
3. **NO PLACEHOLDERS:** Do not use "[No Data]" if you can find the name in the provided list.
4. **STYLE:** Use technical, structured, and strategic persona.

{social_context}
{stats_context}
"""
                
                response = call_gemini_api(draft_prompt, None, image_data=image_data)
                return jsonify({
                    'response': response,
                    'model': LAST_ACTUAL_MODEL,
                    'link_quality': TACTICAL_LINK_LEVEL,
                    'map_context_validated': True
                })
            except Exception as e:
                ColoredLogger.error(f"Prediction analysis error: {e}", "API")
                # Fall through to regular image analysis

        # Detect map from user query for validation
        detected_map = None
        map_keywords = {
            'infernal shrines': 'Infernal Shrines', 'infernalshrines': 'Infernal Shrines',
            'battlefield of eternity': 'Battlefield of Eternity', 'boe': 'Battlefield of Eternity',
            'dragon shire': 'Dragon Shire', 'dragonshire': 'Dragon Shire',
            'blackheart': "Blackheart's Bay", 'blackhearts': "Blackheart's Bay",
            'sky temple': 'Sky Temple', 'skytemple': 'Sky Temple',
            'tomb': 'Tomb of the Spider Queen', 'spider queen': 'Tomb of the Spider Queen',
            'alterac': 'Alterac Pass', 'alterac pass': 'Alterac Pass',
            'volskaya': 'Volskaya Foundry', 'volskaya foundry': 'Volskaya Foundry',
            'garden': 'Garden of Terror', 'garden of terror': 'Garden of Terror',
            'cursed': 'Cursed Hollow', 'cursed hollow': 'Cursed Hollow',
            'towers': 'Towers of Doom', 'towers of doom': 'Towers of Doom',
            'braxis': 'Braxis Holdout', 'braxis holdout': 'Braxis Holdout',
            'hanamura': 'Hanamura Temple', 'hanamura temple': 'Hanamura Temple',
            'warhead': 'Warhead Junction', 'warhead junction': 'Warhead Junction'
        }
        
        message_lower = message.lower()
        for keyword, map_name in map_keywords.items():
            if keyword in message_lower:
                detected_map = map_name
                break

        # Detect role for filtering recommendations
        detected_role = None
        role_keywords = {
            'healer': 'Healer', 'healers': 'Healer', 'support': 'Healer',
            'tank': 'Tank', 'tanks': 'Tank',
            'bruiser': 'Bruiser', 'bruisers': 'Bruiser', 'melee': 'Bruiser',
            'ranged': 'Ranged Assassin', 'ranged assassin': 'Ranged Assassin',
            'assassin': 'Ranged Assassin', 'dps': 'Ranged Assassin'
        }
        for keyword, role in role_keywords.items():
            if keyword in message_lower:
                detected_role = role
                break

        # Helper: Clean text for loose matching
        clean_message = ''.join(c for c in message.lower() if c.isalnum() or c.isspace()).strip()
        
        # Check for Match Analysis intent (keywords requiring deep thought)
        match_analysis_keywords = ['crushed', 'lost', 'won', 'match', 'game', 'how did i', 'analyze', 'breakdown', 'performance']
        is_match_query = any(kw in message.lower() for kw in match_analysis_keywords)

        # If map detected and message is simple (just the map name or keywords), use instant map response
        # This bypasses the heavy ContextCache loading and AI generation for pre-calculated data
        # UPDATE: Now robust to punctuation ("Tomb?" -> "tomb") and avoids hijacking Match Analysis
        is_simple_map_query = detected_map and not is_match_query and (
            clean_message == detected_map.lower().strip() or 
            clean_message in map_keywords or
            clean_message.replace(" ", "") == detected_map.lower().replace(" ", "")
        )
        
        if detected_map and (detected_role or is_simple_map_query):
            response = RESPONSE_CACHE._generate_map_response(detected_map, role_filter=detected_role)
            return jsonify({
                'response': response,
                'model': 'INSTANT',
                'link_quality': 'Fast',
                'map_context_validated': True
            })
        # Enhance system prompt for match analysis queries
        enhanced_context = context or {}
        # match_analysis_keywords and is_match_query already calculated above
        
        if is_match_query and enhanced_context.get('latestMatch'):
            # Add match analysis instructions to context
            enhanced_context['match_analysis_mode'] = True
            enhanced_context['require_detailed_breakdown'] = True
        
        response = call_gemini_api(message, enhanced_context, image_data=image_data)
        
        # Enforce map context validation
        validated_response, has_context = enforce_map_context(response, detected_map)
        
        duration = time.time() - start_time
        if duration > 20:
            ColoredLogger.error(f"⚠️ LATENCY ALERT: {duration:.2f}s | Prompt: {message[:100]}...", "LATENCY")
        
        return jsonify({
            'response': validated_response,
            'model': LAST_ACTUAL_MODEL,
            'link_quality': TACTICAL_LINK_LEVEL,
            'map_context_validated': has_context
        })
    except Exception as e:
        duration = time.time() - start_time
        ColoredLogger.error(f"/api/chat Exception: {e} (Duration: {duration:.2f}s)", "API")
        return jsonify({'error': str(e)}), 500


@app.route('/api/cerebrate/ask', methods=['POST'])
def cerebrate_ask():
    """Route query to multi-agent orchestrator"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        context = data.get('context', {})
        
        # Detect map from user query for fast-path check
        detected_map = None
        message_lower = query.lower()
        map_keywords = {
            'infernal shrines': 'Infernal Shrines', 'infernalshrines': 'Infernal Shrines',
            'battlefield of eternity': 'Battlefield of Eternity', 'boe': 'Battlefield of Eternity',
            'dragon shire': 'Dragon Shire', 'dragonshire': 'Dragon Shire',
            'blackheart': "Blackheart's Bay", 'blackhearts': "Blackheart's Bay",
            'sky temple': 'Sky Temple', 'skytemple': 'Sky Temple',
            'tomb': 'Tomb of the Spider Queen', 'spider queen': 'Tomb of the Spider Queen',
            'alterac': 'Alterac Pass', 'alterac pass': 'Alterac Pass',
            'volskaya': 'Volskaya Foundry', 'volskaya foundry': 'Volskaya Foundry',
            'garden': 'Garden of Terror', 'garden of terror': 'Garden of Terror',
            'cursed': 'Cursed Hollow', 'cursed hollow': 'Cursed Hollow',
            'towers': 'Towers of Doom', 'towers of doom': 'Towers of Doom',
            'braxis': 'Braxis Holdout', 'braxis holdout': 'Braxis Holdout',
            'hanamura': 'Hanamura Temple', 'hanamura temple': 'Hanamura Temple',
            'warhead': 'Warhead Junction', 'warhead junction': 'Warhead Junction'
        }
        
        for keyword, map_name in map_keywords.items():
            if keyword in message_lower:
                detected_map = map_name
                break

        # Check for simple map query fast-path (Robust)
        clean_message = ''.join(c for c in message_lower if c.isalnum() or c.isspace()).strip()
        match_analysis_keywords = ['crushed', 'lost', 'won', 'match', 'game', 'how did i', 'analyze', 'breakdown', 'performance']
        is_match_query = any(kw in message_lower for kw in match_analysis_keywords)
        
        is_simple_map_query = detected_map and not is_match_query and (
            clean_message == detected_map.lower().strip() or 
            clean_message in map_keywords or
            clean_message.replace(" ", "") == detected_map.lower().replace(" ", "")
        )

        if is_simple_map_query:
            response_text = RESPONSE_CACHE._generate_map_response(detected_map)
            return jsonify({
                'response': response_text,
                'success': True,
                'agent': 'INSTANT',
                'model': 'INSTANT',
                'map': detected_map,
                'orchestrator': {
                    'selected_agent': 'INSTANT',
                    'capable_agents': ['INSTANT'],
                    'query': query,
                    'routing_reason': 'Fast-Path: Basic Map Query'
                }
            })

        # Ensure we have the latest cache
        CACHE.load_all()
        
        # Initialize orchestrator if not already done
        global ORCHESTRATOR
        if 'ORCHESTRATOR' not in globals() or ORCHESTRATOR is None:
            from agents.cerebrate_orchestrator import CerebrateOrchestrator
            ORCHESTRATOR = CerebrateOrchestrator(call_gemini_api_fn=call_gemini_api, db_manager=DB)
            
        # Add profile to context
        context['profile'] = CACHE.player_profile
        context['interactions'] = CACHE.player_interactions
        
        # Route query
        response = ORCHESTRATOR.route_query(query, context)
        
        return jsonify(response)
    except Exception as e:
        ColoredLogger.error(f"Orchestrator Error: {e}", "CEREBRATE")
        return jsonify({'error': str(e)}), 500


@app.route('/api/cerebrate/agents', methods=['GET'])
def get_cerebrate_agents():
    """Return all available agents and their capabilities"""
    try:
        # Initialize orchestrator if not already done
        global ORCHESTRATOR
        if 'ORCHESTRATOR' not in globals() or ORCHESTRATOR is None:
            from agents.cerebrate_orchestrator import CerebrateOrchestrator
            ORCHESTRATOR = CerebrateOrchestrator(call_gemini_api_fn=call_gemini_api, db_manager=DB)
            
        agents = ORCHESTRATOR.get_available_agents()
        return jsonify({'agents': agents})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/usage', methods=['GET'])
def get_usage():
    """Return API usage statistics and quota status"""
    try:
        from replay_parser import PARSER_VERSION
        status = QUOTA.get_status()
        
        # Check Service Status
        watcher_pid = os.path.join(os.getcwd(), ".watcher.pid")
        watcher_active = os.path.exists(watcher_pid)
        
        healer_log = os.path.join(os.getcwd(), "healer.log")
        healer_active = False
        if os.path.exists(healer_log):
            mtime = os.path.getmtime(healer_log)
            if time.time() - mtime < 300: # Active in last 5 mins
                healer_active = True

        return jsonify({
            'pipeline_version': PIPELINE_VERSION,
            'parser_version': PARSER_VERSION,
            'current_model': LAST_ACTUAL_MODEL,
            'link_quality': TACTICAL_LINK_LEVEL,
            'quota': status,
            'services': {
                'healer': 'ACTIVE' if healer_active else 'STANDBY',
                'watcher': 'ACTIVE' if watcher_active else 'OFFLINE'
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def load_personalized_brain(context=None):
    """Load all personalized tactical context nodes into a single block"""
    brain = []
    
    # 1. Official Protocols
    if CACHE.brain_protocol: brain.append(f"### CORE PROTOCOL\n{CACHE.brain_protocol}")
    if hasattr(CACHE, 'granular_training') and CACHE.granular_training: brain.append(f"### TACTICAL EXCELLENCE\n{CACHE.granular_training}")
    if hasattr(CACHE, 'social_intelligence') and CACHE.social_intelligence: brain.append(f"### SOCIAL CONTEXT MAPPING\n{CACHE.social_intelligence}")
    if CACHE.verified_data: brain.append(f"### PROJECT MEMORY\n{CACHE.verified_data}")
    
    return "\n\n".join(brain)

@app.route('/api/analyze_image', methods=['POST'])
def analyze_image():
    """Handle multipart image uploads with multi-phase streaming."""
    from flask import stream_with_context, Response
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        image_file = request.files['image']
        user_prompt = request.form.get('prompt', '')
        img_bytes = image_file.read()
        
        import base64
        base64_image = base64.b64encode(img_bytes).decode('utf-8')

        def generate():
            try:
                # 1. FAST PATH: LOCAL MAP STRATEGIES
                map_strategies = {}
                with DB._get_connection() as conn:
                    rows = conn.execute("SELECT * FROM strategies WHERE category = 'map_strategy'").fetchall()
                    for row in rows:
                        try: 
                             # Try both possible column names for compatibility
                             r_dict = dict(row)
                             c_json = r_dict.get('content_json') or r_dict.get('strategy_json')
                             map_strategies[r_dict.get('key') or r_dict.get('name')] = json.loads(c_json)
                        except: continue

                detected_map_fast = None
                if user_prompt:
                    up_low = user_prompt.lower()
                    for m_name in map_strategies.keys():
                        if m_name and m_name.lower() in up_low: 
                            detected_map_fast = m_name
                            break
                
                # Phase 1: INSTANT MAP ASSETS
                if detected_map_fast:
                    s_data = map_strategies[detected_map_fast]
                    msg = f"## {detected_map_fast.upper()} // [DRAFT ASSETS]\n\n"
                    msg += "### 🎯 TOP RECOMMENDATIONS\n"
                    
                    recommendations = []
                    if isinstance(s_data, dict):
                        if 'primary' in s_data:
                            p = s_data['primary']
                            recommendations.append(f"**{p.get('name', 'Primary')}** ({p.get('global', '??')} WR) - {p.get('trigger', 'Strategic choice')}. `{p.get('code', '')}`")
                        if 'backups' in s_data:
                            for b in s_data['backups'][:3]:
                                recommendations.append(f"**{b.get('name', 'Backup')}** ({b.get('global', '??')} WR) - {b.get('trigger', 'Solid alternative')}. `{b.get('code', '')}`")
                    elif isinstance(s_data, list):
                        for item in s_data[:4]:
                            if isinstance(item, dict):
                                recommendations.append(f"**{item.get('hero', item.get('name', 'Hero'))}** - {item.get('verdict', item.get('insight', 'Neural Link asset'))}")
                            else:
                                recommendations.append(str(item))

                    if recommendations:
                        for r in recommendations:
                            msg += f"- {r}\n"
                    else:
                        msg += "- *Retrieving specific neural links...*\n"
                    
                    msg += "\n*Neural Link processing... Deep analysis starting.*"
                    
                    yield json.dumps({
                        "step": "fast_path",
                        "analysis": {"direct_answer": msg},
                        "link_quality": "Fast Cache"
                    }) + "\n"

                # 2. DEEP VISION ANALYSIS
                player_interactions = CACHE.player_interactions or {}
                known_players = []
                for pid, data in list(player_interactions.items())[:20]:
                    name = data.get('name', pid)
                    wr_with = data.get('wins_with', 0)
                    total_with = data.get('total_with', 0)
                    if total_with > 0:
                        known_players.append(f"{name}: {wr_with}/{total_with} with")
                
                social_ctx = "\n\n**KNOWN PLAYERS:**\n" + "\n".join(known_players) if known_players else ""
                
                deep_prompt = f"Analyze this screenshot. User prompt: {user_prompt if user_prompt else 'Perform tactical scan.'}"
                deep_prompt += "\n\nInclude Social Intelligence analysis if any player names match our database."
                deep_prompt += social_ctx
                
                final_response = call_gemini_api(deep_prompt, None, image_data=base64_image)
                
                yield json.dumps({
                    "step": "deep_analysis",
                    "analysis": {"direct_answer": final_response},
                    "link_quality": "High Fidelity"
                }) + "\n"
                
            except Exception as e:
                yield json.dumps({"error": str(e)}) + "\n"
        
        return Response(stream_with_context(generate()), mimetype='application/x-ndjson')
        
    except Exception as e:
        ColoredLogger.error(f"/api/analyze_image Exception: {e}", "API")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'model': GEMINI_MODEL}), 200

@app.route('/api/models', methods=['GET'])
def list_models():
    """List available Gemini models."""
    import requests
    try:
        response = requests.get(
            f'https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}',
            timeout=10
        )
        if response.status_code == 200:
            models = response.json()
            return jsonify(models)
        else:
            return jsonify({'error': f'API Error: {response.status_code}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/<path:filename>')
def serve_data_files(filename):
    """Serve static data files (JSONs)"""
    return send_from_directory('src/data', filename)

@app.route('/api/data/global_hero_stats_stormleague_plus_talents.json', methods=['GET'])
def get_global_hero_stats():
    """Serve global meta stats from SQL (Legacy Path Compatibility)"""
    if CACHE.global_meta:
        return jsonify(CACHE.global_meta)
    
    # Fallback if cache not hot
    with DB._get_connection() as conn:
        rows = conn.execute('SELECT * FROM global_meta_stats').fetchall()
        data = [dict(r) for r in rows]
        # Unpack builds
        for hero in data:
            hero['name'] = hero['hero'] # Map DB 'hero' column to 'name' for frontend compatibility
            hero['builds'] = json.loads(hero['builds_json']) if hero.get('builds_json') else []
        return jsonify(data)

# Image analysis endpoint removed for MVP focus

@app.route('/api/player_profile', methods=['GET'])
def get_player_profile():
    """Serve the player profile from SQLite KV store."""
    data = DB.get_kv('player_profile')
    if data:
        return jsonify(data)
    return jsonify({'error': 'Profile not found'}), 404



# --- MATCH HISTORY MANAGEMENT ---
def load_match_history():
    """Load match history from SQLite."""
    return DB.get_matches(limit=10000)

def save_match_history(history):
    """Save match history to SQLite ONLY (File decommissioned)."""
    for match in history:
        DB.upsert_match(match)
    return True

def load_map_knowledge():
    """Load map knowledge from KV store (migrated from JSON file)"""
    try:
        return DB.get_kv('map_knowledge') or {}
    except:
        return {}


@app.route('/api/rejected_replays')
def get_rejected_replays():
    QM_BLACKLIST_FILE = os.path.join('src', 'data', 'qm_blacklist.json')
    try:
        from pathlib import Path
        import replay_watcher
        watch_dir = replay_watcher.find_replay_dir()
        
        if os.path.exists(QM_BLACKLIST_FILE):
            with open(QM_BLACKLIST_FILE, 'r') as f:
                blacklist = json.load(f)
                
                # Filter: Only show files that actually exist in the watch directory
                active_rejected = []
                for filename in blacklist:
                    if watch_dir and os.path.exists(os.path.join(watch_dir, filename)):
                        active_rejected.append({
                            "filename": filename, 
                            "reason": "Quick Match / ARAM (No Bans Detected)"
                        })
                
                return jsonify({"rejected": active_rejected})
    except Exception as e:
        print(f"Error in rejected_replays: {e}")
    return jsonify({"rejected": []})

def save_map_knowledge(knowledge):
    """Save map knowledge to KV store (migrated from JSON file)"""
    DB.set_kv('map_knowledge', knowledge)

def update_map_knowledge(map_name, result, analysis, bans, hero):
    """Accumulate insights from replay analysis into map knowledge base"""
    knowledge = load_map_knowledge()
    
    # Initialize map if not exists
    if map_name not in knowledge:
        knowledge[map_name] = {
            "total_games": 0,
            "wins": 0,
            "losses": 0,
            "critical_mistakes": [],
            "win_conditions": [],
            "common_bans": {},
            "hero_performance": {},
            "key_learnings": []
        }
    
    map_data = knowledge[map_name]
    
    # Update stats
    map_data["total_games"] += 1
    if result == "WIN":
        map_data["wins"] += 1
    else:
        map_data["losses"] += 1
    
    # Accumulate critical mistakes (keep last 10)
    if analysis.get("critical_mistake"):
        mistake = analysis["critical_mistake"]
        if mistake not in map_data["critical_mistakes"]:
            map_data["critical_mistakes"].append(mistake)
            if len(map_data["critical_mistakes"]) > 10:
                map_data["critical_mistakes"].pop(0)
    
    # Accumulate win conditions (keep last 10)
    win_cond = analysis.get("win_condition") or analysis.get("win_condition_analysis")
    if win_cond:
        if win_cond not in map_data["win_conditions"]:
            map_data["win_conditions"].append(win_cond)
            if len(map_data["win_conditions"]) > 10:
                map_data["win_conditions"].pop(0)
    
    # Track ban frequency
    for ban in bans:
        hero_name = ban.get("hero")
        if hero_name:
            map_data["common_bans"][hero_name] = map_data["common_bans"].get(hero_name, 0) + 1
    
    # Track hero performance
    if hero not in map_data["hero_performance"]:
        map_data["hero_performance"][hero] = {"games": 0, "wins": 0}
    map_data["hero_performance"][hero]["games"] += 1
    if result == "WIN":
        map_data["hero_performance"][hero]["wins"] += 1
    
    save_map_knowledge(knowledge)
    return map_data


@app.route('/api/analyze_replay', methods=['POST'])
def analyze_replay():
    try:
        # Check if file part exists
        if 'file' not in request.files:
             # Fallback to JSON payload if provided (legacy support)
             if request.is_json:
                 return jsonify({"error": "JSON upload deprecated"}), 400
             else:
                 return jsonify({"error": "No replay file provided"}), 400
        
        replay_file = request.files['file']
        if replay_file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Check QM blacklist (similar to duplicate check)
        QM_BLACKLIST_FILE = os.path.join('src', 'data', 'qm_blacklist.json')
        try:
            with open(QM_BLACKLIST_FILE, 'r') as f:
                qm_blacklist = json.load(f)
        except:
            qm_blacklist = []
        
        if replay_file.filename.endswith('.StormReplay'):
            fname_low = replay_file.filename.lower()
            if 'quick match' in fname_low or 'aram' in fname_low:
                ColoredLogger.warn(f"Skipping Non-ranked replay: {replay_file.filename}", "API")
                return jsonify({"error": "Non-ranked game modes are blacklisted"}), 400
            
            # ARAM/Brawl Map Filter
            non_sl_maps = [
                'lost cavern', 'silver city', 'industrial district', 'braxis outpost',
                'checkpoint', 'pull party', 'pool party', 'escape from braxis', 
                'deadman\'s stand', 'sandbox', 'try me', 'blackheart\'s revenge', 
                'haunted mines', 'tutorial', 'hallow\'s end', 'snow brawl'
            ]
            
            fname_flat = fname_low.replace(' ', '')
            if any(m.replace(' ', '') in fname_flat for m in non_sl_maps):
                ColoredLogger.warn(f"Skipping Non-competitive map: {replay_file.filename}", "API")
                return jsonify({"error": "ARAM and specialty maps are blacklisted"}), 400
            
            if 'hanamura' in fname_flat and 'temple' not in fname_flat:
                ColoredLogger.warn(f"Skipping Non-standard Hanamura: {replay_file.filename}", "API")
                return jsonify({"error": "Non-standard Hanamura maps are blacklisted"}), 400

        # Save to temp
        temp_path = os.path.join("/tmp", replay_file.filename)
        replay_file.save(temp_path)
        
        # Silent temp save
        file_size = os.path.getsize(temp_path)
        
        if file_size < 1000:
            # Silent error - file too small
            return jsonify({"error": "Uploaded file is empty or too small"}), 400

        # Parse Replay
        import replay_parser
        parsed_data = replay_parser.parse_replay(temp_path)
        
        # Cleanup temp
        os.remove(temp_path)
        
        # Handle Quick Match rejection
        if parsed_data.get("status") == "rejected":
            # Add to blacklist for future
            if replay_file.filename not in qm_blacklist:
                qm_blacklist.append(replay_file.filename)
                with open(QM_BLACKLIST_FILE, 'w') as f:
                    json.dump(qm_blacklist, f, indent=2)
                if 'Quick Match' in replay_file.filename:
                    ColoredLogger.warn(f"Blacklisted QM replay: {replay_file.filename}", "API")
            return jsonify({"status": "ignored", "message": "Non-Storm League game ignored"}), 200
        
        if parsed_data.get("status") == "error":
             import traceback
             tb = parsed_data.get('traceback', '')
             return jsonify({"error": f"Replay Parse Failed: {parsed_data.get('message')}", "traceback": tb}), 500

        # --- DEDUPLICATION CHECK WITH SMART MERGE ---
        match_id = parsed_data.get('match_id')
        # Check database for existing match
        existing_matches = DB.get_matches(match_id=match_id, limit=1, include_players=True)
        existing_match = existing_matches[0] if existing_matches else None
        
        if existing_match:
            # match_id exists, check if we should update
            # ColoredLogger.info(f"Checking existing match for updates: {match_id}", "API")  # Reduced verbosity
            
            # Check if we have new data that wasn't in the original parse
            has_new_data = False
            
            # Improved Player Merge: Check if new data has talents/stats we are missing OR better quality
            if 'players' in parsed_data:
                old_players = existing_match.get('players', [])
                new_players = parsed_data['players']
                
                # Helper to check for "Rich" talents (actual names vs "Talent X")
                def has_rich_talents(pl_list):
                    for p in pl_list:
                        for t in p.get('talents', []):
                            name = t.get('talent_name', '')
                            # If we see a real name (not "Talent X"), it's rich data
                            if name and not name.startswith('Talent ') and not name.isdigit():
                                return True
                    return False

                old_has_talents = any(len(p.get('talents', [])) > 0 for p in old_players)
                new_has_talents = any(len(p.get('talents', [])) > 0 for p in new_players)
                
                old_is_rich = has_rich_talents(old_players)
                new_is_rich = has_rich_talents(new_players)

                if new_has_talents and not old_has_talents:
                        ColoredLogger.info(f"Found missing talent data. Overwriting player records & Re-Triggering Analysis.")
                        existing_match['players'] = new_players
                        has_new_data = True
                elif new_is_rich and not old_is_rich:
                        ColoredLogger.info(f"Found RICH talent data (Real Names). Overwriting & Re-Triggering Analysis.")
                        existing_match['players'] = new_players
                        has_new_data = True
                elif not old_players:
                        ColoredLogger.info(f"Adding missing 'players' array")
                        existing_match['players'] = new_players
                        has_new_data = True
            
            # Check for advanced_stats improvements
            new_adv = parsed_data.get('advanced_stats', {})
            old_adv = existing_match.get('advanced_stats', {})
            
            # Merge bans if missing
            if new_adv.get('bans') and not old_adv.get('bans'):
                ColoredLogger.info(f"Adding ban data")
                if 'advanced_stats' not in existing_match:
                    existing_match['advanced_stats'] = {}
                existing_match['advanced_stats']['bans'] = new_adv['bans']
                has_new_data = True
            
            # Merge level milestones if missing
            if new_adv.get('level_milestones') and not old_adv.get('level_milestones'):
                ColoredLogger.info(f"Adding level milestone data")
                if 'advanced_stats' not in existing_match:
                    existing_match['advanced_stats'] = {}
                existing_match['advanced_stats']['level_milestones'] = new_adv['level_milestones']
                has_new_data = True

            # NEW: Merge Tactical Telemetry (Pings, Mercs, Structures, Bosses)
            tactical_keys = ['pings', 'merc_captures', 'structure_destructions', 'boss_captures']
            for k in tactical_keys:
                if new_adv.get(k) and (not old_adv.get(k) or (isinstance(old_adv.get(k), list) and len(old_adv.get(k)) < len(new_adv.get(k)))):
                    ColoredLogger.info(f"Adding tactical signal: {k}")
                    if 'advanced_stats' not in existing_match:
                        existing_match['advanced_stats'] = {}
                    existing_match['advanced_stats'][k] = new_adv[k]
                    has_new_data = True
            
            # Check if analysis failed previously
            if existing_match.get('analysis', {}).get('verdict') == 'ANALYSIS FAILED':
                ColoredLogger.info(f"Found previous failed analysis. Re-Triggering Analysis.")
                has_new_data = True
            
            # Match is stable, no new data to add

            # If we added new data, save the updated history
            if has_new_data:
                # IMPORTANT OPTIMIZATION: If we only updated technical data (talents/bans) 
                # but already have a valid analysis, DO NOT re-trigger the expensive AI call.
                # FORCE re-analysis if we just added pings (for forensic quality)
                existing_analysis = existing_match.get('analysis', {})
                has_valid_analysis = existing_analysis and existing_analysis.get('verdict') not in [None, 'ANALYSIS FAILED', 'QUOTA EXCEEDED']
                has_pings_just_added = (new_adv.get('pings') is not None) and (old_adv.get('pings') is None)
                
                if has_valid_analysis and not has_pings_just_added:
                    ColoredLogger.success(f"Merged tech data for {match_id}. Analysis preserved.", "API")
                    # Update DB (database is source of truth)
                    DB.save_match(existing_match)
                    return jsonify({
                        **existing_match,
                        "is_duplicate": True,
                        "note": "Technical Update (Analysis Preserved)"
                    })
                
                ColoredLogger.success(f"Updated existing match with merge. Proceeding to Re-Analysis.")
                # Fall through to Analysis
            else:
                # ColoredLogger.info(f"No new data to add")  # Reduced verbosity
                return jsonify({
                    **existing_match,
                    "is_duplicate": True,
                    "note": "Loaded from Library"
                })

        # --- NEW ANALYSIS PIPELINE CALL ---
        result_json = run_analysis_pipeline(parsed_data)
        
        # --- SAVE RESULT ---
        # Update Map Knowledge
        map_stats = update_map_knowledge(
            map_name=parsed_data.get("map", "Unknown"),
            result=result_json.get("result", "LOSS"), # Pipeline should ideally return the calc result or we pass it
            analysis=result_json,
            bans=parsed_data.get("advanced_stats", {}).get("bans", []),
            hero=parsed_data.get("user_hero_precalc", "Unknown") # We need to pass this or re-extract
        )

        final_response = {
            "id": parsed_data.get('match_id', 'unknown'),
            "map": parsed_data.get("map", "Unknown"),
            "result": "WIN" if parsed_data.get("result") == "Win" else "LOSS", 
            "hero": parsed_data.get("hero", "Unknown"), 
            "talent_build": parsed_data.get("talent_build"),  # NEW: Save user's talent build
            "date": parsed_data.get("timestamp_iso"), # For UI consistency
            "timestamp": parsed_data.get("timestamp_iso"),
            "timestamp_iso": parsed_data.get("timestamp_iso"), # For UI consistency
            "game_length": parsed_data.get("game_length"),
            "analysis": result_json,
            "map_stats": map_stats,
            "players": parsed_data['players'],
            "advanced_stats": parsed_data.get('advanced_stats', {}),
            "link_quality": TACTICAL_LINK_LEVEL # Capture the link level used for analysis
        }
        
        # Save to Database (primary storage)
        DB.save_match(final_response)
        
        # --- REGENERATE MAP KNOWLEDGE & CACHE (Background) ---
        try:
            import subprocess
            api_port = os.environ.get('API_PORT', 5001)
            # Chain the forensics update before the cache generation to ensure fresh shielding data
            # Then notify the API to sync its in-memory context
            chain_cmd = f"python3 scripts/update_nemesis_forensics.py && python3 scripts/generate_map_cache.py && curl -s -X POST http://localhost:{api_port}/api/refresh_context"
            subprocess.Popen(chain_cmd, shell=True, cwd=os.getcwd())
        except Exception as e:
            ColoredLogger.warn(f"Failed to trigger tactical updates: {e}", "API")
        
        return jsonify(final_response)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

def find_original_replay(target_id, date_hint=None):
    """
    Search the standard HotS replay directory for a file matching target_id.
    Uses date_hint (YYYY-MM-DD) to optimize the search if provided.
    """
    import replay_parser
    try:
        from pathlib import Path
        home = Path.home()
        search_paths = [
            home / "Library/Application Support/Blizzard/Heroes of the Storm",
            home / "Documents/Heroes of the Storm",
        ]
        replay_dir = None
        for base_path in search_paths:
            if not base_path.exists(): continue
            for d in base_path.rglob("Replays/Multiplayer"):
                if d.is_dir():
                    replay_dir = d
                    break
            if replay_dir: break
        
        if not replay_dir: return None
        
        # 1. Get all candidate files
        all_files = os.listdir(replay_dir)
        candidates = [f for f in all_files if f.endswith('.StormReplay')]
        
        # 2. Sort/Filter by date_hint to optimize
        if date_hint:
             # date_hint normally ISO: "2025-12-14T01:28:40"
             hint_prefix = date_hint.split('T')[0] # "2025-12-14"
             hint_candidates = [f for f in candidates if hint_prefix in f]
             # Check hint candidates first
             candidates = hint_candidates + [f for f in candidates if f not in hint_candidates]

        # 3. Check headers (fast)
        for filename in candidates:
            filepath = os.path.join(replay_dir, filename)
            # Use the new get_match_id helper to avoid full parse
            if replay_parser.get_match_id(filepath) == target_id:
                return filepath
    except Exception as e:
        ColoredLogger.error(f"Reparse Find Error: {e}", "API")
    return None

@app.route('/api/reparse_match', methods=['POST'])
def reparse_match():
    """Manually trigger a re-parse of a specific match ID"""
    try:
        data = request.get_json()
        match_id = data.get('match_id')
        
        # 1. Find the match in database
        matches = DB.get_matches(match_id=match_id, limit=1, include_players=True)
        if not matches:
            return jsonify({"error": "Match not found"}), 404
        
        match_entry = matches[0]
        
        # 2. NEW: Attempt REAL DEEP RE-PARSE if original file is found
        import replay_parser
        original_file = find_original_replay(match_id, date_hint=match_entry.get('timestamp_iso'))
        
        if original_file:
            ColoredLogger.info(f"Found Original Replay: {os.path.basename(original_file)}. Executing DEEP RE-PARSE...", "API")
            parsed_data = replay_parser.parse_replay(original_file)
            
            if parsed_data.get('status') != 'error':
                 # Use NEW parsed data for analysis
                 parsed_data['match_id'] = match_id
                 
                 # Re-run AI Analysis on fresh parser output
                 result_json = run_analysis_pipeline(parsed_data)
                 
                 # Update database record with fresh metrics (DamageDoneToImmortal, etc.)
                 match_entry.update({
                     "map": parsed_data.get("map"),
                     "hero": parsed_data.get("hero"),
                     "game_length": parsed_data.get("game_length"),
                     "players": parsed_data.get('players'),
                     "advanced_stats": parsed_data.get('advanced_stats'),
                     "analysis": result_json,
                     "pipeline_version": PIPELINE_VERSION
                 })
                 
                 DB.save_match(match_entry)
                 return jsonify(match_entry)
            else:
                 ColoredLogger.warn(f"Deep Re-parse for {match_id} failed: {parsed_data.get('message')}. Falling back to Analysis Re-Analysis.", "API")
        
        # 3. FALLBACK: SHADOW RE-PARSE (Analysis only)
        # Use existing data if source file is missing
        ColoredLogger.info(f"Source file not found for {match_id}. Executing SHADOW RE-PARSE (Analysis only)...", "API")
        
        parsed_data = {
            "match_id": match_entry.get('id'),
            "map": match_entry.get('map'),
            "hero": match_entry.get('hero'),
            "players": match_entry.get('players'),
            "advanced_stats": match_entry.get('advanced_stats'),
            "game_length": match_entry.get('game_length'),
            "result": "Win" if match_entry.get('result') == "WIN" else "Loss",
            "timestamp_utc": match_entry.get('timestamp'),
            "pipeline_version": PIPELINE_VERSION
        }
        
        # Re-Run the Analysis Pipeline
        result_json = run_analysis_pipeline(parsed_data)
        
        # Update and save
        match_entry['analysis'] = result_json
        match_entry['pipeline_version'] = PIPELINE_VERSION
        DB.save_match(match_entry)
        
        return jsonify(match_entry)

    except Exception as e:
        ColoredLogger.error(f"Reparse Error: {e}", "API")
        return jsonify({"error": str(e)}), 500

import os

def load_tactical_memory():
    """Load all tactical memory files from .agent/brain/"""
    memory = {}
    brain_dir = os.path.join('.agent', 'brain')
    
    # Load HERO_STRATEGIES.md
    # Load HERO_STRATEGIES (from SQLite strategies table)
    try:
        with DB._get_connection() as conn:
            rows = conn.execute('SELECT key, content_json FROM strategies WHERE category = ?', ('map_strategy',)).fetchall()
            strategy_text = "HERO STRATEGIES:\n"
            for row in rows:
                try:
                    content = row['content_json']
                    # Handle both string and dict formats
                    if isinstance(content, str):
                        data = json.loads(content)
                    else:
                        data = content
                    
                    # Note: hero_strategies.json format may differ from strategies table format
                    # This is a compatibility layer - adjust as needed based on actual data structure
                    if isinstance(data, dict):
                        for hero, strats in data.items():
                            if isinstance(strats, list):
                                for s in strats:
                                    if isinstance(s, dict):
                                        strategy_text += f"- [{hero} on {s.get('map', 'Any')}]: {s.get('verdict')} | Build: {s.get('build_focus')} | Style: {s.get('playstyle')}\n"
                except (json.JSONDecodeError, TypeError, AttributeError) as parse_err:
                    # Skip malformed entries silently
                    continue
            memory['hero_strategies'] = strategy_text
    except Exception as e:
        # Only log if it's a critical error, not just missing data
        if "no such table" not in str(e).lower() and "no attribute" not in str(e).lower():
            ColoredLogger.warn(f"Hero strategies partially loaded: {str(e)[:50]}")
        memory['hero_strategies'] = strategy_text if 'strategy_text' in locals() else ""

    cheese_path = os.path.join(brain_dir, 'CHEESE_STRATEGIES.md') # Keeping MD for cheese if that's what we use, or update if we have json
    if os.path.exists(cheese_path):
        with open(cheese_path, 'r') as f:
            memory['cheese_strategies'] = f.read()
    
    # Load BAN_RECOMMENDATIONS.md
    ban_path = os.path.join(brain_dir, 'BAN_RECOMMENDATIONS.md')
    if os.path.exists(ban_path):
        with open(ban_path, 'r') as f:
            memory['ban_recommendations'] = f.read()

    # Load GRANULAR_EXCELLENCE_TRAINING.md
    granular_path = os.path.join(brain_dir, 'GRANULAR_EXCELLENCE_TRAINING.md')
    if os.path.exists(granular_path):
        with open(granular_path, 'r') as f:
            memory['granular_excellence'] = f.read()

    # Load GOLD_STANDARDS.md
    gold_path = os.path.join(brain_dir, 'GOLD_STANDARDS.md')
    if os.path.exists(gold_path):
        with open(gold_path, 'r') as f:
            memory['gold_standards'] = f.read()
            
    return memory


LANE_MAPS = {
    "Towers of Doom": [("Bottom Lane", 0, 80), ("Middle Lane", 80, 115), ("Top Lane", 115, 256)],
    "Battlefield of Eternity": [("Bottom Lane", 0, 94), ("Top Lane", 94, 256)],
    "Cursed Hollow": [("Bottom Lane", 0, 80), ("Middle Lane", 80, 115), ("Top Lane", 115, 256)],
    "Infernal Shrines": [("Bottom Lane", 0, 80), ("Middle Lane", 80, 115), ("Top Lane", 115, 256)],
    "Braxis Holdout": [("Bottom Lane", 0, 94), ("Top Lane", 94, 256)],
    "Dragon Shire": [("Bottom Lane", 0, 80), ("Middle Lane", 80, 115), ("Top Lane", 115, 256)],
    "Sky Temple": [("Bottom Lane", 0, 80), ("Middle Lane", 80, 115), ("Top Lane", 115, 256)],
    "Tomb of the Spider Queen": [("Bottom Lane", 0, 80), ("Middle Lane", 80, 115), ("Top Lane", 115, 256)],
    "Garden of Terror": [("Bottom Lane", 0, 80), ("Middle Lane", 80, 115), ("Top Lane", 115, 256)],
    "Alterac Pass": [("Bottom Lane", 0, 80), ("Middle Lane", 80, 115), ("Top Lane", 115, 256)],
    "Volskaya Foundry": [("Bottom Lane", 0, 80), ("Middle Lane", 80, 115), ("Top Lane", 115, 256)],
    "Warhead Junction": [("Bottom Lane", 0, 80), ("Middle Lane", 80, 115), ("Top Lane", 115, 256)],
    "Blackheart's Bay": [("Bottom Lane", 0, 80), ("Middle Lane", 80, 115), ("Top Lane", 115, 256)]
}

def _get_lane_name(map_name, y_coord):
    lanes = LANE_MAPS.get(map_name, [("Bottom Lane", 0, 80), ("Middle Lane", 80, 115), ("Top Lane", 115, 256)])
    for name, low, high in lanes:
        if low <= y_coord < high:
            return name
    return "Unknown Area"

def _get_pos_at_time(timeline, timestamp):
    if not timeline: return None
    # Quick find closest
    best_entry = timeline[0]
    min_diff = abs(timeline[0]['t'] - timestamp)
    for entry in timeline:
        diff = abs(entry['t'] - timestamp)
        if diff < min_diff:
            min_diff = diff
            best_entry = entry
        elif diff > min_diff:
            break # timelines are sorted by t
    return best_entry

def _is_ally(pid1, pid2, parsed_data):
    # PIDs are 1-indexed. Players list is 0-indexed.
    players = parsed_data.get('players', [])
    if 1 <= pid1 <= len(players) and 1 <= pid2 <= len(players):
        return players[pid1-1]['team'] == players[pid2-1]['team']
    return False

def _calculate_leadership_causality(parsed_data, user_pid, user_deaths):
    """
    Analyzes pings to see if they were followed by objective captures.
    Only counts CONSEQUENTIAL pings (Danger, Retreat, Assist Me) - ignores "On My Way" and normal pings.
    """
    adv = parsed_data.get('advanced_stats', {})
    pings = adv.get('pings', [])
    mercs = adv.get('merc_captures', [])
    bosses = adv.get('boss_captures', [])
    map_name = parsed_data.get('map', 'Unknown Map')
    
    user_pings = [p for p in pings if p.get('pid') == user_pid]
    if not user_pings:
        return {
            "total": 0, 
            "consequential": 0,
            "followed": 0, 
            "dead_total": 0, 
            "dead_followed": 0, 
            "ghost_pings": 0, 
            "strategic_pings": 0,
            "lanes": [lane_name for lane_name, _, _ in LANE_MAPS.get(map_name, [])]
        }
    
    # CONSEQUENTIAL ping types: danger, retreat, assist
    # NON-CONSEQUENTIAL: normal, on_my_way (these are just location markers, not actionable)
    consequential_types = {'danger', 'retreat', 'assist'}
    
    # Filter to only consequential pings
    consequential_pings = [p for p in user_pings if p.get('type', 'normal') in consequential_types]
    
    if not consequential_pings:
        return {
            "total": len(user_pings),
            "consequential": 0,
            "followed": 0, 
            "dead_total": 0, 
            "dead_followed": 0, 
            "ghost_pings": 0, 
            "strategic_pings": 0,
            "lanes": [lane_name for lane_name, _, _ in LANE_MAPS.get(map_name, [])]
        }
        
    followed_count = 0
    followed_while_dead = 0
    total_while_dead = 0
    ghost_pings = 0
    strategic_pings = 0
    
    # Pre-process timelines for all players
    timelines = {}
    for p in parsed_data.get('players', []):
        pid = p.get('pid', 0)
        t_line = p.get('pos_timeline', [])
        if pid and t_line:
            timelines[pid] = t_line
            
    # Scale coordinates helper (standard replay scale)
    def s(v): return (v or 0) / 4096.0
    
    objectives = mercs + bosses
    
    for p in consequential_pings:
        p_x, p_y = s(p['point']['x']), s(p['point']['y'])
        p_t = p['timestamp']
        ping_type = p.get('type', 'unknown')
        lane_name = _get_lane_name(map_name, p_y)
        
        # 1. EVALUATE CONTEXT
        nearby_allies = 0
        nearby_enemies = 0
        for other_pid, timeline in timelines.items():
            if other_pid == user_pid: continue
            pos = _get_pos_at_time(timeline, p_t)
            if pos:
                o_x, o_y = s(pos['x']), s(pos['y'])
                dist = ((p_x - o_x)**2 + (p_y - o_y)**2)**0.5
                if dist < 40: # Roughly 1.3 screens
                    if _is_ally(other_pid, user_pid, parsed_data):
                        nearby_allies += 1
                    else:
                        nearby_enemies += 1
        
        # Low context ping: consequential ping (danger/retreat/assist) with no context (no allies, no enemies nearby)
        # This indicates the ping was likely misused or spam
        if nearby_allies == 0 and nearby_enemies == 0:
            ghost_pings += 1
        
        # High context ping: danger ping with enemies nearby, or assist/retreat ping with tactical context
        if ping_type == 'danger' and nearby_enemies > 0:
            strategic_pings += 1
        elif ping_type in ['assist', 'retreat'] and (nearby_allies > 0 or nearby_enemies > 0):
            strategic_pings += 1
        
        # 2. EVALUATE DEAD-STATE
        was_dead = False
        for d in user_deaths:
            respawn_est = 30 
            if d['timestamp'] <= p_t <= (d['timestamp'] + respawn_est):
                was_dead = True
                break
        
        if was_dead: total_while_dead += 1
        
        # 3. EVALUATE FOLLOWERSHIP (only for consequential pings)
        is_followed = False
        for obj in objectives:
            obj_pt = obj.get('point', {})
            obj_x, obj_y = s(obj_pt.get('x')), s(obj_pt.get('y'))
            time_diff = obj['timestamp'] - p_t
            dist = ((p_x - obj_x)**2 + (p_y - obj_y)**2)**0.5
            if dist < 15 and 0 <= time_diff <= 45:
                followed_count += 1
                if was_dead: followed_while_dead += 1
                is_followed = True
                break
                
    return {
        "total": len(user_pings),
        "consequential": len(consequential_pings),
        "followed": followed_count,
        "dead_total": total_while_dead,
        "dead_followed": followed_while_dead,
        "ghost_pings": ghost_pings,
        "strategic_pings": strategic_pings,
        "lanes": [lane_name for lane_name, _, _ in LANE_MAPS.get(map_name, [])]
    }

def _calculate_objective_responsiveness(parsed_data, user_pid, user_hero):
    """
    Analyzes player position relative to map objectives at their spawn/warning times.
    Determines if player was late, present, or ignoring.
    For Warhead Junction, also checks for actual warhead usage (NukeDamageDone).
    """
    adv = parsed_data.get('advanced_stats', {})
    obj_events = adv.get('objective_events', [])
    map_name = parsed_data.get('map', '')
    
    # Special handling for Warhead Junction - check for actual warhead usage
    if map_name == 'Warhead Junction':
        user_player = None
        for p in parsed_data.get('players', []):
            if p.get('pid') == user_pid:
                user_player = p
                break
        
        if user_player:
            stats = user_player.get('stats', {})
            nuke_damage = stats.get('NukeDamageDone', 0)
            if nuke_damage > 0:
                # Player used warheads - this counts as objective participation
                return {
                    "presence_score": 50.0,  # Partial credit for using warheads even if not at spawn
                    "summary": f"Warhead usage detected: {nuke_damage:,} nuke damage dealt. Player collected and used warheads.",
                    "analysis_list": [{
                        "time": "N/A",
                        "event": "Warhead Usage",
                        "user_dist": 0,
                        "user_status": "Used Warhead",
                        "allies_present": "N/A"
                    }],
                    "total_events": 1,
                    "warhead_usage": True,
                    "nuke_damage": nuke_damage
                }
    
    # Special handling for Battlefield of Eternity - check for Immortal Damage
    if map_name == 'Battlefield of Eternity':
        user_player = None
        for p in parsed_data.get('players', []):
            if p.get('pid') == user_pid:
                user_player = p
                break
        
        if user_player:
            stats = user_player.get('stats', {})
            immortal_dmg = stats.get('DamageDoneToImmortal', 0) or stats.get('ImmortalDamage', 0)
            if immortal_dmg > 0:
                return {
                    "presence_score": min(100.0, 40.0 + (immortal_dmg / 2000.0)), # Base 40 + scaling
                    "summary": f"Immortal participation detected: {immortal_dmg:,} damage dealt to objective.",
                    "analysis_list": [{
                        "time": "N/A",
                        "event": "Immortal Objective",
                        "user_dist": 0,
                        "user_status": "DPS Active",
                        "allies_present": "N/A"
                    }],
                    "total_events": 1
                }
    
    if not obj_events:
        return {"presence_score": 0, "summary": "No map objectives recorded.", "analysis_list": []}
        
    timelines = {p.get('pid'): p.get('pos_timeline', []) for p in parsed_data.get('players', []) if p.get('pid')}
    def s(v): return (v or 0) / 4096.0
    
    analysis = []
    present_count = 0
    total_relevant = 0
    
    # We look for "Start" and "End" pairs or meaningful announcements
    # e.g., "ObjectiveWarning" -> "ObjectiveLabelUpdate" (captured)
    
    for i, event in enumerate(obj_events):
        ename = event['event_name']
        if 'Warning' in ename or 'Spawn' in ename:
            total_relevant += 1
            t_start = event['timestamp']
            pt = event.get('point', {})
            obj_x, obj_y = s(pt.get('x')), s(pt.get('y'))
            
            # If coordinates are missing (0,0), this might be a global event without location
            if obj_x == 0 and obj_y == 0: continue
            
            # Check user position at t_start
            u_pos = _get_pos_at_time(timelines.get(user_pid), t_start)
            u_dist = 999
            if u_pos:
                u_dist = ((obj_x - s(u_pos['x']))**2 + (obj_y - s(u_pos['y']))**2)**0.5
            
            # Find the "Conclusion" of this objective - usually the next capture event
            t_end = t_start + 60 # Default window
            conclusion_event = None
            for next_ev in obj_events[i+1:i+10]:
                if any(kw in next_ev['event_name'] for kw in ['Update', 'Captured', 'Complete']):
                    conclusion_event = next_ev
                    t_end = next_ev['timestamp']
                    break
            
            # Check user position at t_end
            u_pos_end = _get_pos_at_time(timelines.get(user_pid), t_end)
            u_dist_end = 999
            if u_pos_end:
                u_dist_end = ((obj_x - s(u_pos_end['x']))**2 + (obj_y - s(u_pos_end['y']))**2)**0.5
            
            # State Logic
            status = "Ignoring"
            if u_dist < 25: 
                status = "Present (Elite Response)"
                present_count += 1
            elif u_dist_end < 25:
                status = "Arrived Late"
                present_count += 0.5
            elif u_dist_end < 45:
                status = "Just Arriving (Contest Fail)"
                
            # Team Context
            team_avg_dist = 0
            allies_present = 0
            for pid, t_line in timelines.items():
                if pid == user_pid: continue
                if _is_ally(pid, user_pid, parsed_data):
                    pos = _get_pos_at_time(t_line, t_start)
                    if pos:
                        d = ((obj_x - s(pos['x']))**2 + (obj_y - s(pos['y']))**2)**0.5
                        if d < 25: allies_present += 1
            
            analysis.append({
                "time": format_mm_ss(t_start),
                "event": ename,
                "user_dist": round(u_dist, 1),
                "user_status": status,
                "allies_present": allies_present
            })
            
    presence_pct = round((present_count / total_relevant * 100), 1) if total_relevant > 0 else 0
    
    # Format a string for the AI prompt
    summary_lines = []
    for a in analysis:
        summary_lines.append(f"- At {a['time']} ({a['event']}): {user_hero} was {a['user_dist']} units away. Status: {a['user_status']}. ({a['allies_present']} allies nearby).")
        
    return {
        "presence_score": presence_pct,
        "summary": "\n".join(summary_lines) if summary_lines else "No objective windows analyzed.",
        "analysis_list": analysis,
        "total_events": total_relevant
    }

def run_analysis_pipeline(parsed_data):
    """
    Core Logic for generating the AI Match Verdict.
    Encapsulates all Prompt Engineering and Module D checks.
    """
    map_name = parsed_data.get("map", "Unknown Map")
    print(f"--- [FORENSIC SIGNAL START: {map_name}] ---")
    
    # Identify User
    user_name = parsed_data.get("user_name", "Unknown Player")
    if user_name == "Unknown Player":
        # Heuristic: Try to find 'jmoncayo' or specific known aliases, or fallback
        # In saved history, we don't strictly store who the 'user' was in a marked field sometimes.
        # Let's try to infer from the list or default to the first player if desperate, 
        # BUT 'analyze_replay' had logic to find 'jmoncayo'.
        # We should replicate that or assume the caller passed it.
        # Better: Look for the player flagged as 'user' in players list if possible? 
        # The parser marks `name` but not `is_user`.
        # Let's scan for our known aliases.
        known_aliases = [
            os.environ.get('PLAYER_NAME', 'Discerning'),
            os.environ.get('PLAYER_BATTLE_TAG', 'Discerning#2567'),
            'jmoncayo', 
            'Cerebrate'
        ]
        for p in parsed_data.get('players', []):
            if any(alias.lower() in p['name'].lower() for alias in known_aliases):
                user_name = p['name']
                break
    
    # Identify user hero early for addressing
    user_hero = parsed_data.get('hero', 'Unknown Hero')
    # Calculate Result and Team
    result = "LOSS"
    user_player_data = None
    user_pid = 0
    for i, p in enumerate(parsed_data.get('players', [])):
        if p['name'] == user_name:
            user_player_data = p
            user_pid = p.get('pid', i + 1)
            break
            
    if not user_player_data:
        # Fallback to identify by hero if name mismatch
        for i, p in enumerate(parsed_data.get('players', [])):
            if p['hero'] == user_hero:
                user_player_data = p
                user_pid = p.get('pid', i + 1)
                user_name = p['name']
                break
    
    user_team = user_player_data.get('team') if user_player_data else None

    if user_player_data and 'win' in user_player_data:
        result = "WIN" if user_player_data['win'] else "LOSS"
    else:
        result = "WIN" if parsed_data.get("result") == "Win" else "LOSS"

    # --- COMPLEX DATA EXTRACTION (Format Strings) ---
    adv = parsed_data.get("advanced_stats", {})
    bans_list = adv.get("bans", [])
    milestones = adv.get("level_milestones", {})
    game_len_sec = parsed_data.get("game_length", 0)
    game_len_min = game_len_sec / 60 if game_len_sec > 0 else 1
    # If hero is still 'Unknown Hero' or 'Unknown', try to get it from user_player_data if it exists
    if (user_hero == 'Unknown Hero' or user_hero == 'Unknown') and user_player_data:
        user_hero = user_player_data.get('hero', 'The Player')
    elif not user_hero:
        user_hero = 'The Player'
    
    bans_str = ", ".join([f"{b['hero']} (Match Start)" for b in bans_list]) if bans_list else "None recorded"
    
    levels_str = ""
    for team_id, levels in milestones.items():
        lvl10 = levels.get('10', 'Never')
        lvl20 = levels.get('20', 'Never')
        levels_str += f"Team {team_id}: Lvl 10 @ {lvl10}, Lvl 20 @ {lvl20}\n"

    def format_mm_ss(seconds):
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}:{s:02d}"

    # Leadership signals: Pings
    pings_list = adv.get("pings", [])
    player_pings = {i+1: 0 for i in range(16)} # Range matches stats_data
    team_pings = {0: 0, 1: 0}
    for p_event in pings_list:
        p_id = p_event.get('pid')
        if p_id in player_pings:
            player_pings[p_id] += 1
            # Find team for this PID
            if p_id <= len(parsed_data.get('players', [])):
                ptr = parsed_data['players'][p_id-1]
                team_pings[ptr['team']] += 1

    # Create a mapping of PID -> Hero for kill detection and calculate team totals
    pid_to_hero = {i+1: p['hero'] for i, p in enumerate(parsed_data.get('players', []))}
    
    # Aggregated Stats for Competitive Context
    team_totals = {0: {'HeroDamage': 0, 'Healing': 0, 'XP': 0, 'TeamfightDamageTaken': 0}, 
                   1: {'HeroDamage': 0, 'Healing': 0, 'XP': 0, 'TeamfightDamageTaken': 0}}
    team_maxes = {0: {'HeroDamage': 0, 'Healing': 0, 'XP': 0}, 
                  1: {'HeroDamage': 0, 'Healing': 0, 'XP': 0}}

    for p in parsed_data.get('players', []):
        t = p['team']
        st = p.get('stats', {})
        team_totals[t]['HeroDamage'] += st.get('HeroDamage', 0)
        team_totals[t]['Healing'] += st.get('Healing', 0)
        team_totals[t]['XP'] += st.get('ExperienceContribution', 0)
        team_totals[t]['TeamfightDamageTaken'] += st.get('TeamfightDamageTaken', 0)
        
        for k in ['HeroDamage', 'Healing', 'ExperienceContribution']:
            val = st.get(k, 0)
            if val > team_maxes[t].get(k, 0):
                team_maxes[t][k] = val

    players_str = ""
    for i, p in enumerate(parsed_data.get('players', [])):
        is_user = "**[YOU]**" if p['name'] == user_name else ""
        
        # Explicit Team Labeling
        team_role = "UNKNOWN"
        if user_team is not None:
            team_role = "ALLY" if p['team'] == user_team else "ENEMY"

        # Merge kv_stats and standard stats to ensure map objectives are caught
        s = p.get('kv_stats', {}).copy()
        s.update(p.get('stats', {}))
        death_events = p.get('death_events', [])
        
        # Format death string with KILLED BY info and POSITIONING context
        death_entries = []
        for d in death_events:
            tag = " [OUTNUMBERED]" if d.get('outnumbered') else ""
            dist = d.get('dist_to_nearest_ally')
            # 30 units is roughly one screen distance; >35 is isolated
            dist_tag = f" [EXTENDED dist:{dist}]" if dist and dist > 35 else ""
            
            killer_pid = d.get('killer_pid')
            killer_hero = pid_to_hero.get(killer_pid, "Unknown")
            killer_type = d.get('killer_type', "Unknown")
            
            death_detail = f"by {killer_hero}" if killer_hero != "Unknown" else f"by {killer_type}"
            death_entries.append(f"{format_mm_ss(d['timestamp'])} {death_detail}{tag}{dist_tag}")
        
        death_final_str = f" (Context: {', '.join(death_entries)})" if death_entries else (f" ({s.get('Deaths', 0)} Total Deaths)" if s.get('Deaths', 0) > 0 else " (0 Deaths)")
        
        # Strategic Context: Group Objective Time with Deaths for 'Strategic Sacrifice' detection
        obj_time = max(s.get('TimeInTemple', 0), s.get('TimeOnPoint', 0))
        tf_damage = s.get('TeamfightHeroDamage', 0)
        tf_taken = s.get('TeamfightDamageTaken', 0)
        clutch_heals = s.get('ClutchHealsPerformed', 0)
        self_heal = s.get('SelfHealing', 0)
        mercs = s.get('MercCampCaptures', 0)
        escapes = s.get('EscapesPerformed', 0)
        globes = s.get('RegenGlobes', 0)
        outnumbered = s.get('OutnumberedDeaths', 0)
        vehicles = s.get('DragonNumberOfDragonCaptures', 0) or s.get('GardenTrifterKilled', 0)
        tributes = s.get('RavenTributesCollected', 0)
        gems = s.get('GemsTurnedIn', 0)
        doubloons = s.get('BlackheartDoubloonsTurnedIn', 0)
        seeds = s.get('SeedsTurnedIn', 0)
        altars = s.get('AltarsCaptured', 0)
        
        map_obj_str = ""
        if tributes: map_obj_str += f" | Tributes: {tributes}"
        if gems: map_obj_str += f" | Gems: {gems}"
        if doubloons: map_obj_str += f" | Doubloons: {doubloons}"
        if seeds: map_obj_str += f" | Seeds: {seeds}"
        if altars: map_obj_str += f" | Altars: {altars}"
        if vehicles: map_obj_str += f" | Vehicles: {vehicles}"
        
        # BoE / Objective Specifics
        immortal_dmg = s.get('DamageDoneToImmortal', 0) or s.get('ImmortalDamage', 0)
        if immortal_dmg: map_obj_str += f" | Immortal Dmg: {immortal_dmg:,}"
        
        # CC Breakdown
        stuns = s.get('TimeStunningEnemyHeroes', 0)
        roots = s.get('TimeRootingEnemyHeroes', 0)
        silences = s.get('TimeSilencingEnemyHeroes', 0)
        cc_str = f" | CC Secs (Stun: {stuns}s, Root: {roots}s, Silence: {silences}s)" if (stuns or roots or silences) else ""
        
        downtime = s.get('TimeSpentDead', 0)
        downtime_str = f" | Total Downtime: {format_mm_ss(downtime)}" if downtime > 0 else ""

        ping_count = player_pings.get(i+1, 0)

        macro_anchor_stats = f"Obj Time: {format_mm_ss(obj_time)} | Mercs: {mercs}{map_obj_str} | Globes: {globes} | Escapes: {escapes} | Pings: {ping_count} | Outnumbered Deaths: {outnumbered}/{s.get('Deaths', 0)}{cc_str}{downtime_str}"

        # Talent Extraction: TIER-AWARE DEDUPLICATION
        # Parser logs multiple events for the same choice or misclicks.
        # We process them to keep only the final unique selections.
        talents = p.get('talents', [])
        clean_build = {}
        for t in talents:
            name = t.get('talent_name')
            if name:
                # We use the name as a key to ensure uniqueness.
                # We use the name as a key to ensure uniqueness.
                # In a more advanced version, we'd map these to specific Tiers (1, 4, 7).
                timestamp_str = format_mm_ss(t.get('timestamp', 0))
                clean_build[name] = f"{name} (@{timestamp_str})"
        
        # Priority Scrubbing for Kharazim (L1 Traits are mutually exclusive)
        if p['hero'] == 'Kharazim':
            if 'KharazimInsightTalent' in clean_build:
                clean_build.pop('KharazimIronFistsTalent', None)
                clean_build.pop('KharazimTranscendenceTalent', None)
            if 'KharazimElevenSidedStrikeTalent' in clean_build:
                clean_build.pop('KharazimSevenSidedStrike', None)
                clean_build.pop('KharazimDivinePalm', None)
                clean_build.pop('KharazimWayoftheHundredFistsTalent', None)
            
        talents_str = " | ".join(clean_build.values()) if clean_build else "No talents recorded"

        # MVP Detection
        is_mvp = " [OFFICIAL MVP]" if s.get('EndOfMatchAwardMVPBoolean') else ""
        
        # Competitive Percentages
        t_id = p['team']
        pct_hero_dmg = (s.get('HeroDamage', 0) / team_totals[t_id]['HeroDamage'] * 100) if team_totals[t_id]['HeroDamage'] > 0 else 0
        pct_soak = (s.get('XP', 0) / team_totals[t_id]['XP'] * 100) if team_totals[t_id]['XP'] > 0 else 0
        pct_tf_soaked = (s.get('TeamfightDamageTaken', 0) / team_totals[t_id]['TeamfightDamageTaken'] * 100) if team_totals[t_id]['TeamfightDamageTaken'] > 0 else 0

        stats_block = (
            f"KDA: {s.get('Kills', 0)}/{s.get('Deaths', 0)}/{s.get('Assists', 0)}{death_final_str}\n"
            f"   - **STRATEGIC CONTEXT**: {macro_anchor_stats}\n"
            f"   - Hero Dmg: {s.get('HeroDamage', 0)} ({pct_hero_dmg:.1f}% of Team) | TF Dmg: {tf_damage}\n"
            f"   - Healing: {s.get('Healing', 0)} (Self: {self_heal} | Clutch: {clutch_heals})\n"
            f"   - XP: {s.get('XP', 0)} ({pct_soak:.1f}% of Team) | Pure Soak (Minion XP): {s.get('PureSoak', 0)}\n"
            f"   - Breakdown: HeroXP: {s.get('HeroXP', 0)} | StructureXP: {s.get('StructureXP', 0)} | TF Dmg Taken: {tf_taken} ({pct_tf_soaked:.1f}% of Team)\n"
            f"   - **BUILD**: {talents_str}"
        )
        players_str += f"\nPlayer {i+1} ({p['hero']}) {is_user}{is_mvp} - Team: {team_role}\n{stats_block}\n"
    # print(f"DEBUG ROSTER:\n{players_str}")

    # --- OBSOLETE BUILD DETECTOR: DISABLED (PREVENTS MOCK DATA HALLUCINATIONS) ---
    obsolete_context_str = "Status: STABLE"
    robust_build_str = "Build analysis pending."

    
    # --- LOAD TACTICAL MEMORY ---
    tactical_memory = load_tactical_memory()
    hero_strategies_context = tactical_memory.get('hero_strategies', '')
    cheese_strategies_context = tactical_memory.get('cheese_strategies', '')
    
    # Extract boss captures from advanced_stats
    boss_captures = parsed_data.get('advanced_stats', {}).get('boss_captures', [])
    boss_context_str = ""
    if boss_captures:
        boss_context_str = "\n**BOSS CAPTURES DETECTED:**\n"
        for boss in boss_captures:
            boss_type = boss.get('boss_type', 'Boss')
            timestamp = boss.get('timestamp', 0)
            team_id = boss.get('captured_by_team', 'Unknown')
            team_label = "ALLY" if str(team_id) == str(user_team) else "ENEMY"
            
            kill_speed = boss.get('kill_speed_seconds')
            mm_ss = format_mm_ss(timestamp)
            if kill_speed:
                boss_context_str += f"- [{team_label}] {boss_type} captured at {mm_ss} (Kill Speed: {kill_speed}s)\n"
            else:
                boss_context_str += f"- [{team_label}] {boss_type} captured at {mm_ss}\n"
    
    # --- PROMPT ---
    map_knowledge = load_map_knowledge().get(map_name, {})
    knowledge_str = f"Wins: {map_knowledge.get('wins',0)}/{map_knowledge.get('total_games',0)}"

    # Format game length
    game_len_formatted = format_mm_ss(game_len_sec)

    # RESTORED: Calculate leadership causality
    user_deaths = user_player_data.get('stats', {}).get('Deaths', 0) if user_player_data else 0
    leadership = _calculate_leadership_causality(parsed_data, user_pid, user_deaths)

    leadership_str = "Leadership analysis decommissioned."

    # RESTORED: Calculate objective responsiveness and warhead usage
    obj_resp = _calculate_objective_responsiveness(parsed_data, user_pid, user_hero)
    warhead_usage_note = obj_resp.get('warhead_note', '')

    obj_resp_str = f"{obj_resp['summary']}{warhead_usage_note}"
    
    # Mercenary Insights
    merc_captures = parsed_data.get('advanced_stats', {}).get('merc_captures', [])
    user_merc_count = user_player_data.get('stats', {}).get('MercCampCaptures', 0) if user_player_data else 0
    team_merc_count = sum(p.get('stats', {}).get('MercCampCaptures', 0) for p in parsed_data.get('players', []) if p.get('team') == user_team)
    
    merc_insights = f"Personal Captures: {user_merc_count} | Team Total: {team_merc_count}"

    # Forensic Debug (only log to file, not console)
    if pings_list:
        debug_msg = f"DEBUG: Constructing prompt for {user_hero} with {len(pings_list)} match pings. Leadership: {leadership_str}. Obj Score: {obj_resp['presence_score']}%"
        # Only write to log file, don't spam console
        try:
            with open('leadership_debug.log', 'a') as f_log:
                f_log.write(debug_msg + "\n")
        except:
            pass  # Silently fail if log file can't be written

    prompt = f"""
    ## {map_name}
    *{knowledge_str} | Efficiency Protocol Active*

    **MAP TOPOGRAPHY**: Lanes: {', '.join(leadership['lanes'])}
    **OBJECTIVE RESPONSIVENESS (TIMELINE)**:
    {obj_resp_str}
    
    **MATCH RESULT**: {result} (Game Length: {game_len_formatted})
    
    **CRITICAL OUTPUT RULES:**
    0. **TONE**: Brutally honest High-Elo Coach. Use simple, direct cause-and-effect.
    1. **ADDRESS BY HERO**: Use the hero name **{user_hero}** naturally for all references to the player. (Do not force double asterisks if it interferes with grammar).
    2. **DATA ADHERENCE**: State ONLY numbers and verified events.
    3. **PHRASE BLACKLIST**: NEVER use "resource conversion", "throughput", "poke damage", "neutralize", "capitalize", "likely", "probably", "appears to", "incurred deaths", "offset", "indicates", "indication".
    4. **PING FORENSICS**: Ping analysis is decommissioned. Do not report ping statistics.
    5. **OBJECTIVE CADENCE**: Analyze **OBJECTIVE RESPONSIVENESS (TIMELINE)**. 
        - **WARHEAD JUNCTION SPECIAL CASE**: If the analysis shows warhead usage (NukeDamageDone > 0), the player DID participate in objectives by collecting and using warheads.
        - **UI WARNING**: Objective Time (TimeOnPoint/TimeInTemple) is ONLY tracked on specific maps like Sky Temple or Braxis. On other maps (Cursed Hollow, Spider Queen), '0:00' is a placeholder. 
        - **GROUND TRUTH**: Use the specific counts (Tributes, Gems, etc.) and the **OBJECTIVE RESPONSIVENESS** timeline as the true measure of participation.
        - If low objective presence was INTENTIONAL (macro-focused strategy that enabled win), explain it as "intentional macro prioritization" or "strategic trade-off".
        - If Total Events == 0, DO NOT report findings.
        - **CRITICAL**: If you mention low objective presence, you MUST explain whether it was intentional/strategic or a mistake.
    6. **DETAIL LEVEL**: CLINICAL. Do not give 1-sentence summaries. Explain the *sequence* of events that led to the result.
       **CRITICAL**: Your summary MUST be **EXACTLY 3-5 sentences** with causal analysis. 
       **FORBIDDEN**: Do NOT write summaries that are just chronological event lists like "At 3:08, Hero died. At 5:47, Hero died..." 
       **REQUIRED**: You MUST provide ANALYSIS, not just a timeline. Explain WHY events happened, what they caused, and their tactical significance.
       Single-sentence summaries are REJECTED. Event-list summaries are REJECTED.

    **GOLD STANDARD REFERENCE (LOSS) - THIS IS THE MINIMUM QUALITY BAR:**
    "dominance": "**Kharazim** led match Experience (27k) with **22,040 Pure Soak**.",
    "summary": "TIMING FAILURE. **Kharazim** died at 19:16 (isolated) near the Boss Pit, 10 seconds before the objective spawned. This forced a 4v5 defense which collapsed. Earlier deaths at 05:46 and 07:32 fed critical XP during the rotation phase, putting the team down a Talent Tier at the 12:00 mark.",
    "win_condition": "Level 20 deficit at 14:44. Enemy team secured Level 16 first, allowing them to invade and steal the Boss at 15:00. We never recovered map control.",
    "tactical_breakdown": "Deaths at 17:45 (dist < 10.0) confirm core formation attrition.",
    
    **GOLD STANDARD REFERENCE (WIN) - ADDITIONAL EXAMPLE:**
    "summary": "MACRO ENGINE ENGAGED. On Towers of Doom, you and **Jaina** demonstrated elite **Throughput Distribution**. By allowing a High-Efficiency Camper (**Jaina**) to manage 8 Sapper captures (**24 Core Damage**), you were freed to generate **16,834 Experience** and anchor the lane-states with **9,144 Pure Soak**. This synergy secured 36 total Core Shots from mercenaries alone, turning the map into a structured ammunition factory while you maintained the team's level advantage.",
    
    7. **MERCENARY CADENCE**:
        - Analyze **MERCENARY INSIGHTS**. If Personal Captures > 0, emphasize the player's macro impact.
        - If Personal Captures == 0 but Team Total is high, acknowledge the team's macro performance but note the player's different focus.
        
    8. **TALENT BUILD ANALYSIS**:
        - **CRITICAL**: Level 1 talents are chosen BEFORE the game starts (in draft). NEVER analyze Level 1 talent choices as if they were chosen mid-game or connect them to in-game struggles.
        - **CRITICAL**: Do NOT analyze talent choices at timestamps like "0:24" or "0:30" - these are just when talents are recorded in the replay, not when they were chosen.
        - **CRITICAL**: Level 1 talents cannot "exacerbate struggles" or "prioritize X over Y" during the game - they're pre-game choices.
        - Only analyze LATE GAME talent timing (Level 13, 16, 20):
        - If Level 13, 16, or 20 talents are missing/late compared to game time, call it out.
        - Example: "Level 16 Talent not picked until 18:00 (Late Power Spike)."
        - **FORBIDDEN**: Do NOT criticize Level 1-7 talent choices based on game events that happened after they were chosen. These are draft decisions, not in-game mistakes.

    **KNOWN STRATEGIES (MEMORY):**
    {hero_strategies_context}
    {cheese_strategies_context}
    
    {levels_str}
    {boss_context_str}
    
    **MERCENARY INSIGHTS**:
    {merc_insights}
    
    **ROSTER STATS:**
    {players_str}
    
    **DIRECTIVE:**
    Analyze **{user_hero}**'s performance. Generate a HIGH-QUALITY, STRUCTURED analysis following this EXACT format:
    
    **OUTPUT FORMAT (CRITICAL - FOLLOW THIS STRUCTURE):**
    
    1. **ANALYSIS VERDICT**: ["Objective Alpha" | "Macro Anchor" | "Solid" | "Feeder" | "Passenger" | "MVP" | "Empty Suit" | "Coin Flip" | "Shotcaller" | "Mechanic"]
       **CRITICAL**: If verdict is "Solid" or "Macro Anchor" but you list a critical mistake, you MUST explain in the summary WHY the mistake was acceptable or if it was actually a strategic choice.
    
    2. **SUMMARY**: This is the MAIN analytical narrative. **CRITICAL: MUST FOLLOW GOLD STANDARD FORMAT**
       - **FORBIDDEN FORMATS (DO NOT DO THIS - THESE WILL BE REJECTED):**
         * ❌ "At 3:08, Jaina died to Malfurion. At 5:47, Jaina died to Li-Ming..." (Just listing events chronologically)
         * ❌ "At 8:34, Gazlowe died to Kel'Thuzad. At 10:50, Gazlowe died again..." (Event list format)
         * ❌ "Jaina participated in kills at 6:22, 7:56..." (Just listing timestamps)
         * ❌ Simple event timeline without analysis
         * ❌ Single sentence summaries
         * ❌ Two-sentence summaries
         * **ANY SUMMARY STARTING WITH "At XX:XX" WILL BE AUTOMATICALLY REJECTED AND REGENERATED**
       - **REQUIRED ELEMENTS:**
         * **EXACTLY 3-5 sentences** with causal analysis (Explain WHY events happened).
         * Balanced use of technical data (Pure Soak, XP, etc.) only where relevant.
         * Cohesive narrative flow. Avoid mere event lists.
       - **GOLD STANDARD EXAMPLE:**
         "RESOURCE SUPREMACY. Despite the loss, your performance was a macroeconomic masterclass. Your 27,439 Experience Contribution contained **22,040 Pure Soak** (Isolated Minion XP), proving you were the team's primary engine for level progression. However, a critical **Vehicle Allocation** error occurred: piloting the Dragon Knight (10:04 capture) as a solo-healer. This choice traded ~5,200 Healing Per Minute (HPM) for siege damage—equivalent to removing 1.5x of a Valla's health pool from the team's sustain capacity."
       - **ANOTHER GOLD STANDARD EXAMPLE (MATCH THIS QUALITY):**
         "Functioning as a combat anchor, Kharazim utilized the Insight build to convert offensive pressure into 61,325 Unified Throughput. Your 3,305 Pure Soak (Minion-based XP) represents a strategic trade-off for 00:00 of Temple Occupancy, effectively buying macro-space for teammates to harvest 38k combined XP. This match proves that objective control is the secondary engine that permits teammates to win via lane soak."
       - **YOUR SUMMARY MUST MATCH THIS LEVEL OF DETAIL AND ANALYSIS.**
       - **IF YOUR SUMMARY IS JUST A LIST OF EVENTS, IT IS WRONG. START OVER.**
    
    3. **KEY INSIGHTS**: Extract and format ONLY significant metrics.
       - IMPORTANT: If a metric is 0, or "0", DO NOT include it in key_insights. Only report metrics that represent an event or achievement.
       - **Downtime**: Use the exact 'Total Downtime' value (MM:SS) provided in the STRATEGIC CONTEXT. Omit if 0:00.
       - **True Soak**: Minion XP (Pure Soak number). Omit if 0.
       - **Kill Streak**: Longest streak (from stats). Omit if < 5.
       - **Mercenary Camps**: Personal camps captured (from MERCENARY INSIGHTS). Omit if 0.
       - Format as structured data points. Omit the key/value pair entirely from JSON if the value is zero or non-significant.
    
    4. **CRITICAL MISTAKE**: Single impactful error with tactical context.
       **REQUIRED FORMAT**: Must be 1-2 sentences explaining WHAT the mistake was, WHEN it happened (timestamp), WHY it was impactful, and HOW it contributed to the loss. Include specific details like hero names, locations, or tactical context.
       **EARLY GAME DEATH ANALYSIS**: Deaths before 3:00 are rarely "critical objective vulnerabilities" since objectives haven't spawned yet. Early deaths are usually just feeding XP. Only call them critical if they directly led to a talent tier deficit (e.g., "Death at 2:45 fed enough XP for enemy to hit Level 4 first at 3:12, losing the first objective").
       **FORBIDDEN**: 
       - Do NOT use generic phrases like "Low participation" or "No critical mistakes detected" without context.
       - Do NOT claim early deaths (< 3:00) "permitted critical objective vulnerabilities" unless objectives were actually active or the death directly caused a talent tier deficit.
       - Do NOT say "allies to peel" when you mean "enemies to peel" - check your wording.
       - Do NOT describe mistakes without connecting them to the loss outcome.
       **EXAMPLES OF GOOD CRITICAL MISTAKES**:
       - "Death at 19:16 (isolated) near the Boss Pit, 10 seconds before the objective spawned, forcing a 4v5 defense which collapsed and led to the final push."
       - "Death at 2:45 fed 400 XP to Sylvanas, enabling enemy team to reach Level 4 at 3:12 (8 seconds before us), securing first objective uncontested and establishing early map control that snowballed."
       - "Failed to rotate to the top Shrine at 8:34, allowing enemy team to secure Punisher uncontested and push through both forts, creating a structural deficit that proved insurmountable."
       **CRITICAL CONSISTENCY RULE**: If your verdict is "Solid", "Macro Anchor", or "Objective Alpha" (positive verdicts), and you list a critical mistake like "Low participation in team fights", you MUST explain in the summary WHY this was acceptable OR if it was actually a strategic choice. Do NOT contradict yourself - if low teamfight participation enabled a macro win, explain it as "intentional macro prioritization" or "strategic trade-off", not just a mistake. The summary must reconcile the positive verdict with the listed mistake. If it was a mistake that led to the loss, explain how the good macro performance was insufficient to overcome the mistake.
    
    5. **WIN CONDITION**: Level Milestone causality with specific timestamps and analysis.
       **CRITICAL**: Only analyze meaningful level milestones: Level 4, 7, 10, 13, 16, 20. NEVER analyze Level 1 - it's reached immediately and has no tactical significance.
       **FORBIDDEN**: 
       - Do NOT mention "Level 1" or "reaching Level 1" as a win condition or power advantage.
       - Do NOT use placeholder text like "Never", "Never, Never", "Unknown", "N/A", or "TBD" for timestamps.
       - If you cannot determine the exact timestamp from the data, use the game length or a reasonable estimate based on context (e.g., "mid-game" or "late-game").
       Format: "The team [suffered/achieved] a [decisive/critical] [power deficit/advantage] by [falling behind/reaching] Level [4/7/10/13/16/20] at [MM:SS], [time delta] after/before the enemy team. This [deficit/advantage] was [secured/caused] by [specific hero/event] [outperforming/underperforming] in [specific metric] while [your team/you] [underperformed/outperformed] in [specific area]."
       **REQUIRED**: Timestamps MUST be valid MM:SS format (e.g., "10:34", "15:22"). If level milestone timing is unclear, analyze based on game length and context rather than using placeholder text.
    
    6. **TACTICAL BREAKDOWN**: Positional Forensics + Objective Responsiveness + Death Analysis.
        - Analyze death events with positional context. 
        - **OUTNUMBERED DEATHS**: These are signs of ISOLATION, POOR POSITIONING, or TEAM COLLAPSE. Never describe them as "proactive" or "aggressive" unless it directly led to a teamfight win.
        - **DISTANCE (dist)**: Distances > 30 confirm isolation. Distances < 15 confirm core formation attrition.
        - Example: "The death at [MM:SS] ([dist] units from nearest ally) confirms severe isolation during a critical rotation."
    
    Return strict JSON:
    {{
            "verdict": "...",
            "summary": "...",
            "key_insights": {{
                "kill_streak": "...",
                "mercenary_camps": "...",
                "downtime": "...",
                "true_soak": "..."
            }},
            "critical_mistake": "...",
            "win_condition": "...",
            "tactical_breakdown": "..."
    }}
    """
    # CRITICAL: Use raw_mode=True for clinical analysis.
    # raw_mode=False injects chat personas which conflict with strict JSON formatting required for the UI tiles.
    response = call_gemini_api(prompt, raw_mode=True, silent=True)
    try:
        res_text = str(response).strip()
        
        # Check if response is an error message before parsing
        if res_text.startswith("API Error") or res_text.startswith("Error calling"):
             return {
                 "verdict": "QUOTA EXCEEDED", 
                 "summary": "AI Quota reached. Historical analysis is queued.", 
                 "win_condition_analysis": res_text,
                 "dominance": "High Frequency Ingestion",
                 "areas_for_improvement": "Wait for API reset."
             }

        if "```json" in res_text:
            res_text = res_text.split("```json")[1].split("```")[0].strip()
        elif "```" in res_text:
            res_text = res_text.split("```")[1].split("```")[0].strip()
            
        result = json.loads(res_text)
        return result

    except Exception as e:
        ColoredLogger.error(f"Analysis Pipeline Parse Error: {e}", "API")
        return {
            "verdict": "ANALYSIS FAILED", 
            "summary": "Full re-parse failed. Likely malformed AI response.", 
            "win_condition_analysis": str(response)
        }




        
        # --- SAVE TO HISTORY ---


@app.route('/api/match_history', methods=['GET'])
def get_match_history():
    """High-speed match history retrieval via SQLite with frontend compatibility."""
    limit = request.args.get('limit', default=100, type=int)
    offset = request.args.get('offset', default=0, type=int)
    hero = request.args.get('hero')
    map_name = request.args.get('map')
    match_id = request.args.get('id')
    
    # Database manager handles all frontend compatibility (date/timestamp_iso normalization, JSON parsing, etc.)
    matches = DB.get_matches(limit=limit, offset=offset, hero=hero, map_name=map_name, match_id=match_id)
    
    return jsonify(matches)



@app.route('/api/player_interactions', methods=['GET'])
def get_player_interactions():
    """Serve social intelligence from SQL-backed cache"""
    try:
        interactions = CACHE.player_interactions
        if not interactions:
            interactions = DB.get_kv('player_interactions') or {}
        
        # Load Neural Intelligence Briefs from database
        neural_briefs = DB.get_kv('neural_intelligence_briefs') or {}
        for player_id, player_data in interactions.items():
            if player_id in neural_briefs:
                player_data['aiStrategy'] = neural_briefs[player_id]
        
        return jsonify(interactions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/player_interactions/<player_id>/neural_brief', methods=['POST'])
def save_neural_brief(player_id):
    """Save Neural Intelligence Brief for a player"""
    try:
        data = request.get_json()
        brief = data.get('brief', '')
        
        if not brief:
            return jsonify({"error": "Brief content required"}), 400
        
        # Load existing briefs
        briefs = DB.get_kv('neural_intelligence_briefs') or {}
        briefs[player_id] = brief
        
        # Save to database
        DB.set_kv('neural_intelligence_briefs', briefs)
        
        # Update cache
        if player_id in CACHE.player_interactions:
            CACHE.player_interactions[player_id]['aiStrategy'] = brief
        
        return jsonify({"success": True, "message": "Neural Intelligence Brief saved"})
    except Exception as e:
        ColoredLogger.error(f"Failed to save neural brief: {e}", "API")
        return jsonify({"error": str(e)}), 500


@app.route('/api/cerebrate_config', methods=['GET'])
def get_cerebrate_config():
    """Serve cerebrate config from database"""
    try:
        config = DB.get_kv('cerebrate_config') or {}
        
        # Inject Mission Cache (Pre-calculated tactical briefings)
        mission_cache_raw = DB.get_kv('map_recommendations_cache') or {}
        config['mission_cache'] = mission_cache_raw.get('recommendations', {})

        # Ensure active_season exists with defaults
        if 'active_season' not in config:
            config['active_season'] = {
                'slug': 'season_2025_3',
                'name': 'Season 3 2025',
                'start_date': '2025-09-01'
            }
        return jsonify(config)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/arsenal', methods=['GET'])
def get_arsenal():
    """Return Arsenal analytics - elite performers and secret weapons"""
    try:
        # Load from KV store instead of JSON file
        cache = DB.get_kv('map_recommendations_cache') or {}
        
        arsenal_picks = []
        secret_weapons = []
        
        # Sleeper heroes (undervalued by community)
        sleeper_heroes = ['Gazlowe', 'Malthael', 'Rehgar', 'Lt. Morales', 'Brightwing', 'Raynor']
        
        for map_name, data in cache['recommendations'].items():
            for hero_data in data['heroes']:
                hero = hero_data['hero']
                wr = hero_data['wr']
                games = hero_data['games']
                source = hero_data['source']
                
                # Arsenal criteria: 55%+ WR, 10+ games, sleeper pick
                if wr >= 55 and games >= 10 and hero in sleeper_heroes:
                    value_score = wr * (games / 10)  # WR weighted by sample size
                    
                    arsenal_picks.append({
                        'map': map_name,
                        'hero': hero,
                        'wr': wr,
                        'games': games,
                        'source': source,
                        'value_score': value_score
                    })
                
                # Secret weapons: 60%+ WR, 20+ games
                if wr >= 60 and games >= 20:
                    secret_weapons.append({
                        'map': map_name,
                        'hero': hero,
                        'wr': wr,
                        'games': games
                    })
        
        # Sort by value score
        arsenal_picks.sort(key=lambda x: -x['value_score'])
        secret_weapons.sort(key=lambda x: -x['wr'])
        
        return jsonify({
            'arsenal_picks': arsenal_picks[:15],  # Top 15
            'secret_weapons': secret_weapons[:6]  # Top 6
        })
        
    except Exception as e:
        ColoredLogger.error(f"Arsenal Error: {e}", "API")
        return jsonify({'error': str(e)}), 500


@app.route('/api/update_match', methods=['POST'])
def update_match():
    """Update match with user insights/corrections"""
    try:
        data = request.json
        match_id = data.get('match_id')
        insight_type = data.get('type')  # 'player_note', 'ai_correction', 'challenge'
        insight_data = data.get('data')
        
        if not match_id or not insight_type or not insight_data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Load match from database
        matches = DB.get_matches(match_id=match_id, limit=1)
        if not matches:
            return jsonify({'error': 'Match not found'}), 404
        
        match = matches[0]
        
        # Add insights array if it doesn't exist
        if 'insights' not in match.get('analysis', {}):
            match['analysis']['insights'] = []
        
        # Add new insight with timestamp
        from datetime import datetime
        match['analysis']['insights'].append({
            'type': insight_type,
            'data': insight_data,
            'timestamp': datetime.now().isoformat()
        })
        # Save back to database
        DB.save_match(match)
        return jsonify({'success': True, 'message': 'Match updated'})
        
    except Exception as e:
        ColoredLogger.error(f"{e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/challenge_match', methods=['POST'])
def challenge_match():
    """
    Re-processes a match replay to verify a user's challenge.
    Instead of blindly updating, this re-runs the parser with improved logic.
    """
    try:
        data = request.get_json()
        match_id = data.get('match_id')
        replay_path = data.get('replay_path')
        
        if not match_id:
            return jsonify({'error': 'Missing match_id'}), 400

        # Resolve path: Priority 1: Direct path from request (if exists)
        # Priority 2: Local library path (from history)
        final_path = None
        if replay_path and os.path.exists(replay_path):
            final_path = replay_path
        else:
            # Look up in database for local_replay_path
            matches = DB.get_matches(match_id=match_id, limit=1)
            match_record = matches[0] if matches else None
            if match_record:
                l_path = match_record.get('local_replay_path')
                if l_path and os.path.exists(l_path):
                    final_path = l_path
                    ColoredLogger.info(f"Found replay in local library: {final_path}")
                elif l_path:
                    # Try relative path check if stored as absolute
                    rel_path = os.path.basename(l_path)
                    lib_path = os.path.join('src', 'data', 'replays', rel_path)
                    if os.path.exists(lib_path):
                        final_path = lib_path
                        ColoredLogger.info(f"Found replay in relative local library: {final_path}")

        if final_path:
            ColoredLogger.info(f"Auditing replay: {final_path}")
            
            # Re-run parser
            from replay_parser import parse_replay
            new_data = parse_replay(final_path)
            
            if not new_data:
                 return jsonify({'error': 'Re-parsing failed'}), 500

            # Load existing match from database
            matches = DB.get_matches(match_id=match_id, limit=1)
            if not matches:
                return jsonify({'error': 'Original match record not found'}), 404
            
            match = matches[0]
                    # Preserve the ID/Analysis but update stats/result
                    # We merge the new parse data into the existing record
            match.update(new_data)
            match['id'] = match_id # Ensure ID persistence
            match['analysis'] = match.get('analysis', {}) # Keep existing AI analysis
            
            # Save to database
            DB.save_match(match)

            return jsonify({
                'success': True, 
                'message': f"Replay verified! Result validated as: {new_data.get('result')}",
                'new_result': new_data.get('result'),
                'verified': True
            })

        else:
             return jsonify({'error': 'Replay file not found for verification. Cannot audit.'}), 404

    except Exception as e:
        ColoredLogger.error(f"challenging match: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    """Update player profile with new notes/preferences"""
    try:
        data = request.json
        update_type = data.get('type')  # 'hero_note', 'map_preference', 'role_preference'
        update_data = data.get('data')
        
        if not update_type or not update_data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Load player profile (SQL)
        profile = DB.get_kv('player_profile') or {}
        
        # Update based on type
        if update_type == 'hero_note':
            hero = update_data.get('hero')
            note = update_data.get('note')
            
            # Find hero in slumping or strong heroes
            for hero_list in ['slumping_heroes', 'strong_heroes']:
                heroes = profile.get('storm_league_audit', {}).get(hero_list, [])
                for h in heroes:
                    if h['hero'] == hero:
                        h['notes'] = note
                        break
        
        elif update_type == 'map_preference':
            map_name = update_data.get('map')
            preference = update_data.get('preference')  # 'strong' or 'weak'
            
            if 'map_preferences' not in profile:
                profile['map_preferences'] = {'strong': [], 'weak': []}
            
            # Remove from opposite list
            opposite = 'weak' if preference == 'strong' else 'strong'
            if map_name in profile['map_preferences'].get(opposite, []):
                profile['map_preferences'][opposite].remove(map_name)
            
            # Add to preference list
            if map_name not in profile['map_preferences'].get(preference, []):
                profile['map_preferences'][preference].append(map_name)
        
        elif update_type == 'hero_build':
            hero = update_data.get('hero')
            build_code = update_data.get('build_code')  # Format: "T1234567" or "[T1234567,Hero]"
            note = update_data.get('note', '')  # Optional note about the build
            
            # Extract build code if in format [T1234567,Hero]
            if build_code and build_code.startswith('[') and ']' in build_code:
                import re
                match = re.search(r'T(\d{1,7})', build_code)
                if match:
                    build_code = f"T{match.group(1)}"
            
            # Initialize hero_builds if not exists
            if 'hero_builds' not in profile:
                profile['hero_builds'] = {}
            
            if hero not in profile['hero_builds']:
                profile['hero_builds'][hero] = {}
            
            # Save preferred build
            profile['hero_builds'][hero]['preferred'] = build_code
            if note:
                profile['hero_builds'][hero]['note'] = note
            profile['hero_builds'][hero]['last_updated'] = datetime.now().isoformat()
            
            ColoredLogger.signal("PROFILE", f"Updated {hero} preferred build: {build_code}")
        
        # Save updated profile
        from datetime import datetime
        profile['last_updated'] = datetime.now().isoformat()
        
        DB.set_kv('player_profile', profile)
        CACHE.player_profile = profile  # Update cache
        
        return jsonify({'success': True, 'message': 'Profile updated'})
        
    except Exception as e:
        ColoredLogger.error(f"{e}")
        return jsonify({'error': str(e)}), 500

# --- Audit Endpoint ---
@app.route('/api/audit/run', methods=['POST'])
def run_audit():
    try:
        data = request.json or {}
        season = data.get('season', '2025 Season 3') # Default to current
        
        ColoredLogger.info(f"for {season}")
        client = HeroesProfileClient()
        engine = AuditEngine(client)
        
        report_md = engine.run_audit(season)
        
        # Save report
        # Clean filename manually to avoid chinese characters helper above if needed
        clean_season = season.replace(" ", "-").lower()
        filename = f"storm-league-audit-{clean_season}.md"
        
        filepath = os.path.join("reports", filename)
        with open(filepath, "w") as f:
            f.write(report_md)
            
        return jsonify({
            "status": "success", 
            "message": "Audit completed successfully",
            "report_path": filepath,
            "report_content": report_md
        })
        
    except Exception as e:
        ColoredLogger.error(f"{e}")
        return jsonify({"status": "error", "error": str(e)}), 500

# --- REPLAY WATCHER CONTROL ---
import subprocess
import signal

watcher_process = None

@app.route('/api/health', methods=['GET'])
def api_health():
    """API health check endpoint"""
    return jsonify({'status': 'ok'}), 200

def _find_watcher_pids():
    """Helper to find all PIDs for any active replay_watcher logic (including children)."""
    pids = []
    
    # 1. Primary: Check PID file for instant lookup
    pid_file = ".watcher.pid"
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                pid_content = f.read().strip()
                if pid_content:
                    pid = int(pid_content)
                    # Use ps -p [pid] -o state=,command= to get both state and command
                    # State 'Z' means zombie
                    check = subprocess.run(['ps', '-p', str(pid), '-o', 'state=,command='], capture_output=True, text=True)
                    if check.returncode == 0:
                        parts = check.stdout.strip().split(maxsplit=1)
                        if len(parts) >= 2:
                            state, cmd_out = parts[0], parts[1].lower()
                            if 'z' not in state.lower() and 'python' in cmd_out and 'replay_watcher.py' in cmd_out:
                                return [pid]
        except: pass

    # 2. Fallback: Full process scan
    try:
        # ps -A -o pid,state,command
        cmd = ['ps', '-A', '-o', 'pid,state,command']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if 'replay_watcher.py' not in line:
                continue
                
            parts = line.split(maxsplit=2)
            if len(parts) < 3: continue
            
            pid_str, state, command = parts[0], parts[1].lower(), parts[2].lower()
            
            # Exclude zombies
            if 'z' in state:
                continue
                
            # Exclude wrappers
            if any(x in command for x in ['concurrently', 'node', 'npm', 'grep']):
                continue
                
            # Must contain python execution or the script itself directly
            if 'python' in command or 'replay_watcher.py' in command:
                try:
                    pids.append(int(pid_str))
                except: pass
    except Exception as e:
        ColoredLogger.error(f"PID Scan Error: {e}", "API")
        
    return list(set(pids)) # Unique PIDs only

def _update_watcher_status_file(status, message=None, current_file=None):
    """Helper to write to the watcher status file for UI tracking."""
    try:
        status_file = '.watcher_status.json'
        with open(status_file, 'w') as f:
            json.dump({
                "status": status,
                "message": message or status,
                "current_file": current_file,
                "timestamp": time.time()
            }, f)
    except: pass

def _get_watcher_state_summary():
    """Shared logic to aggregate all watcher status data into a single object."""
    # 1. Check active processes
    pids = _find_watcher_pids()
    is_running = len(pids) > 0
    
    # Read processing status from watcher status file
    processing_status = None
    replay_count = 0
    try:
        status_file = '.watcher_status.json'
        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                processing_status = json.load(f)
    except: pass
    
    # Try to count replays from processed log
    try:
        processed_log = '.processed_replays.txt'
        if os.path.exists(processed_log):
            with open(processed_log, 'r') as f:
                replay_count = len([line for line in f if line.strip()])
    except: pass
    
    # Read activity log
    activity_log = []
    try:
        activity_file = '.watcher_activity.json'
        if os.path.exists(activity_file):
            with open(activity_file, 'r') as f:
                activity_log = json.load(f)
    except: pass
    
    # Sanitize activity log: if watcher is not running, no item should be "active" or "scanning"
    if not is_running and activity_log:
        for activity in activity_log:
            active_statuses = ['checking', 'uploading', 'pending']
            if activity.get('status') in active_statuses:
                activity['status'] = 'stopped'
                activity['message'] = 'WATCHER STOPPED'
                if 'stages' in activity:
                    for s_key in activity['stages']:
                        if activity['stages'][s_key] == 'active':
                            activity['stages'][s_key] = 'skipped'
    
    return {
        'running': is_running,
        'replay_count': replay_count,
        'activities': activity_log,
        'processing': processing_status
    }

@app.route('/api/watcher/status', methods=['GET'])
def watcher_status():
    """Check if replay watcher is running and get processing status"""
    return jsonify(_get_watcher_state_summary())

@app.route('/api/watcher/start', methods=['POST'])
def start_watcher():
    """Start the replay watcher process"""
    global watcher_process
    import subprocess
    import sys
    
    # Pre-flight Check: Is there already a watcher running elsewhere?
    targets = _find_watcher_pids()
    if targets:
        ColoredLogger.info(f"Targeting active links for renewal (PIDs: {targets})...", "API")
        for pid in targets:
            try: os.kill(pid, signal.SIGKILL)
            except: pass

    try:
        # Ensure log directory exists
        os.makedirs('logs', exist_ok=True)
        
        # Start watcher as subprocess
        # Create new process group with start_new_session to facilitate clean shutdown
        with open('logs/watcher.log', 'a') as log_file:
            watcher_process = subprocess.Popen(
                ['python3', 'replay_watcher.py'],
                stdout=log_file,
                stderr=log_file,
                cwd=os.getcwd(),
                env=os.environ.copy(),
                start_new_session=True 
            )
        
        ColoredLogger.success(f"Intelligence Link established (PID: {watcher_process.pid})", "API")
        
        # Write initial status
        _update_watcher_status_file('starting', "Establishing Neural Link...")
        
        # Return summary so UI updates instantly
        summary = _get_watcher_state_summary()
        summary['status'] = 'started'
        summary['pid'] = watcher_process.pid
        summary['running'] = True # Force true as we just started it
        return jsonify(summary)
    except Exception as e:
        watcher_process = None
        ColoredLogger.error(f"Intelligence Link failure: {e}", "API")
        return jsonify({'error': str(e)}), 500

@app.route('/api/watcher/stop', methods=['POST'])
def stop_watcher():
    """Stop the replay watcher process with extreme prejudice"""
    global watcher_process
    import subprocess
    import signal
    
    try:
        # 1. Surgical Strike: Kill the tracked object if it exists
        if watcher_process is not None:
            try:
                # Kill process group if possible
                pgid = os.getpgid(watcher_process.pid)
                os.killpg(pgid, signal.SIGKILL)
            except:
                try: watcher_process.kill()
                except: pass
            watcher_process = None

        # 2. Scorched Earth: Hunt down ALL instances including orphans
        targets = _find_watcher_pids()
        killed_count = 0
        for pid in targets:
            try:
                ColoredLogger.info(f"Terminating Watcher PID: {pid}", "API")
                os.kill(pid, signal.SIGKILL)
                killed_count += 1
            except Exception as e:
                ColoredLogger.error(f"Failed to kill {pid}: {e}", "API")
        
        # 3. Cleanup Telemetry Lock
        pid_file = ".watcher.pid"
        if os.path.exists(pid_file):
            try: os.remove(pid_file)
            except: pass

        # 4. Update status file to clear UI immediately 
        _update_watcher_status_file('stopped', "Watcher manually disabled")

        # Give the OS a millisecond to reap the processes before we scan again
        time.sleep(0.05)
        
        # Return summary so UI updates instantly
        summary = _get_watcher_state_summary()
        summary['status'] = 'stopped'
        summary['running'] = False # Hard-force false to ensure UI flips
        return jsonify(summary)
            
    except Exception as e:
        ColoredLogger.error(f"Watcher Termination Fault: {e}", "API")
        return jsonify({'status': 'stopped', 'running': False, 'error': str(e)})




@app.route('/api/contest_analysis', methods=['POST'])
def contest_analysis():
    """
    Allow users to contest an AI analysis verdict.
    This triggers a re-analysis with enhanced context and user feedback.
    """
    try:
        data = request.json
        match_id = data.get('match_id')
        user_feedback = data.get('feedback')
        
        if not match_id or not user_feedback:
            return jsonify({'error': 'Missing match_id or feedback'}), 400
        
        # Load match from database
        matches = DB.get_matches(match_id=match_id, limit=1)
        if not matches:
            return jsonify({'error': 'Match not found'}), 404
        
        target_match = matches[0]
        
        # Ensure analysis exists
        if 'analysis' not in target_match:
            target_match['analysis'] = {}
        
        if 'contested_analyses' not in target_match['analysis']:
            target_match['analysis']['contested_analyses'] = []
        
        from datetime import datetime
        contest_entry = {
            'timestamp': datetime.now().isoformat(),
            'original_verdict': target_match.get('analysis', {}).get('verdict'),
            'user_feedback': user_feedback,
            'status': 'pending_review'
        }
        target_match['analysis']['contested_analyses'].append(contest_entry)
        target_match['analysis']['needs_review'] = True
        
        # Save to database
        DB.save_match(target_match)
        
        ColoredLogger.success(f"Analysis contested for match {match_id}", "API")
        return jsonify({
            'success': True,
            'message': 'Analysis contested. Match flagged for review.',
            'contest_id': len(target_match['contested_analyses']) - 1
        })
        
    except Exception as e:
        ColoredLogger.error(f"Contest Analysis Error: {e}", "API")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ═══════════════════════════════════════════════════════════════
# CEREBRATE PREDICTION TRACKING
# ═══════════════════════════════════════════════════════════════

@app.route('/api/cerebrate/log_prediction', methods=['POST'])
def log_cerebrate_prediction():
    """Log a Cerebrate prediction for tracking"""
    try:
        data = request.json
        
        # Load existing log
        log_path = 'src/data/cerebrate_advice_log.json'
        try:
            with open(log_path, 'r') as f:
                log = json.load(f)
        except FileNotFoundError:
            log = {
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "total_predictions": 0,
                    "total_correct": 0,
                    "accuracy": 0.0,
                    "version": "1.0"
                },
                "predictions": [],
                "stats": {}
            }
        
        # Generate prediction ID
        pred_id = f"pred_{str(len(log['predictions']) + 1).zfill(3)}"
        
        # Create prediction entry
        prediction = {
            "id": pred_id,
            "timestamp": datetime.now().isoformat(),
            "map": data.get('map'),
            "your_hero": data.get('your_hero'),
            "your_team": data.get('your_team', []),
            "enemy_team": data.get('enemy_team', []),
            "prediction": {
                "win_probability": data.get('win_probability'),
                "reasoning": data.get('reasoning'),
                "recommended_pick": data.get('recommended_pick'),
                "recommended_build": data.get('recommended_build'),
                "key_advantages": data.get('key_advantages', []),
                "key_threats": data.get('key_threats', [])
            },
            "actual_result": None,
            "analysis": None
        }
        
        # Add to log
        log["predictions"].append(prediction)
        log["metadata"]["total_predictions"] += 1
        log["metadata"]["last_updated"] = datetime.now().isoformat()
        
        # Save log
        with open(log_path, 'w') as f:
            json.dump(log, f, indent=2)
        
        ColoredLogger.success(f"Logged prediction {pred_id} for {data.get('map')}", "CEREBRATE")
        return jsonify({
            'success': True,
            'prediction_id': pred_id,
            'message': 'Prediction logged successfully'
        })
        
    except Exception as e:
        ColoredLogger.error(f"Log Prediction Error: {e}", "CEREBRATE")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cerebrate/update_prediction_result', methods=['POST'])
def update_cerebrate_prediction_result():
    """Update a prediction with actual match result"""
    try:
        data = request.json
        pred_id = data.get('prediction_id')
        outcome = data.get('outcome')  # "WIN" or "LOSS"
        followed_advice = data.get('followed_advice', False)
        
        # Load log
        log_path = 'src/data/cerebrate_advice_log.json'
        with open(log_path, 'r') as f:
            log = json.load(f)
        
        # Find prediction
        prediction = None
        for pred in log["predictions"]:
            if pred["id"] == pred_id:
                prediction = pred
                break
        
        if not prediction:
            return jsonify({'error': 'Prediction not found'}), 404
        
        # Update result
        prediction["actual_result"] = {
            "outcome": outcome,
            "followed_advice": followed_advice,
            "used_recommended_build": data.get('used_recommended_build', False),
            "match_duration": data.get('match_duration'),
            "kda": data.get('kda')
        }
        
        # Calculate analysis
        win_prob = prediction["prediction"]["win_probability"]
        predicted_win = win_prob > 50
        actual_win = outcome == "WIN"
        
        prediction["analysis"] = {
            "prediction_correct": predicted_win == actual_win,
            "variance": "upset" if (predicted_win != actual_win) else "expected",
            "upset": (win_prob < 50 and actual_win) or (win_prob > 50 and not actual_win),
            "confidence_level": "high" if abs(win_prob - 50) > 20 else ("moderate" if abs(win_prob - 50) > 10 else "low")
        }
        
        # Update metadata
        if prediction["analysis"]["prediction_correct"]:
            log["metadata"]["total_correct"] += 1
        
        log["metadata"]["accuracy"] = (log["metadata"]["total_correct"] / log["metadata"]["total_predictions"] * 100) if log["metadata"]["total_predictions"] > 0 else 0
        log["metadata"]["last_updated"] = datetime.now().isoformat()
        
        # Save log
        with open(log_path, 'w') as f:
            json.dump(log, f, indent=2)
        
        ColoredLogger.success(f"Updated prediction {pred_id}: {outcome}", "CEREBRATE")
        return jsonify({
            'success': True,
            'prediction': prediction,
            'accuracy': log["metadata"]["accuracy"]
        })
        
    except Exception as e:
        ColoredLogger.error(f"Update Prediction Error: {e}", "CEREBRATE")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cerebrate/stats', methods=['GET'])
def get_cerebrate_stats():
    """Get Cerebrate prediction statistics"""
    try:
        log_path = 'src/data/cerebrate_advice_log.json'
        with open(log_path, 'r') as f:
            log = json.load(f)
        
        # Calculate stats
        total = log["metadata"]["total_predictions"]
        correct = log["metadata"]["total_correct"]
        accuracy = log["metadata"]["accuracy"]
        
        # Count upsets
        upsets = [p for p in log["predictions"] if p.get("analysis", {}).get("upset", False)]
        
        # By map stats
        by_map = {}
        for pred in log["predictions"]:
            map_name = pred["map"]
            if map_name not in by_map:
                by_map[map_name] = {"predictions": 0, "correct": 0, "accuracy": 0}
            
            by_map[map_name]["predictions"] += 1
            if pred.get("analysis", {}).get("prediction_correct", False):
                by_map[map_name]["correct"] += 1
            
            by_map[map_name]["accuracy"] = (by_map[map_name]["correct"] / by_map[map_name]["predictions"] * 100) if by_map[map_name]["predictions"] > 0 else 0
        
        # By hero stats
        by_hero = {}
        for pred in log["predictions"]:
            hero = pred.get("your_hero")
            if not hero or hero == "Unknown":
                continue
            
            if hero not in by_hero:
                by_hero[hero] = {"predictions": 0, "correct": 0, "wins": 0, "losses": 0}
            
            by_hero[hero]["predictions"] += 1
            if pred.get("analysis", {}).get("prediction_correct", False):
                by_hero[hero]["correct"] += 1
            
            if pred.get("actual_result", {}).get("outcome") == "WIN":
                by_hero[hero]["wins"] += 1
            elif pred.get("actual_result", {}).get("outcome") == "LOSS":
                by_hero[hero]["losses"] += 1
        
        return jsonify({
            'metadata': log["metadata"],
            'total_predictions': total,
            'total_correct': correct,
            'accuracy': accuracy,
            'upset_wins': len(upsets),
            'upset_percentage': (len(upsets) / total * 100) if total > 0 else 0,
            'by_map': by_map,
            'by_hero': by_hero,
            'recent_predictions': log["predictions"][-5:]  # Last 5
        })
        
    except Exception as e:
        ColoredLogger.error(f"Get Stats Error: {e}", "CEREBRATE")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# SCREENSHOT VERIFICATION ENDPOINTS
# ============================================================================

@app.route('/api/extract_stats_from_screenshot', methods=['POST'])
def extract_stats_from_screenshot():
    """Extract full profile stats from screenshot using Gemini Vision"""
    try:
        data = request.json
        image_data = data.get('image', '')
        
        if not image_data:
            return jsonify({"success": False, "error": "No image provided"}), 400
        
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        prompt = """Analyze this Heroes of the Storm screenshot. It is either a **PROFILE PAGE**, **VICTORY SCREEN**, or **RANKED LOBBY**.

DETECT THE SCREEN TYPE:
1. **TALENT_BUILDS**: Look for rows of round talent icons. Key distinctive feature is a column "Copy Build" or "Copy" with a dark blue button, and build codes like `[T123...]`. The header is usually Teal/Green.
2. **HEROES_PROFILE**: Look for a dense data table with columns "Map", "Games", "Win Rate". The distinct visual style is a **Dark Teal/Cyan Header** row on a dark background. It clearly looks like a WEBSITE, not the game client.
3. **VICTORY_SCREEN**: standard game screen with "Summary/Stats/Talents" tabs top center, and a rank circle.
4. **PROFILE_PAGE**: standard game screen with "STATISTICS" panel, "MAP RECORD", and usually a 3D Hero Model on the left.
5. **RANKED_LOBBY**: Ranked matchmaking screen with rank badge, "Ready" button, and rank points display.

---
IF VICTORY SCREEN:
1. Extract **Rank**: The tier and division (e.g. "Bronze 1", "Silver 5").
2. Extract **Rank Points**: The raw number (e.g. "200", "850").
3. Extract **Result**: "Victory" or "Defeat".
4. Extract **Hero**: The hero shown (e.g. "Rehgar", "Valla").

---
IF RANKED LOBBY / RANK SCREEN:
1. Extract **Rank**: The tier and division (e.g. "Silver 5").
2. Extract **Rank Points**: Current rank points (e.g. "29").
3. Extract **Points Required for Promotion**: Look for text like "X Rank Points required for promotion" or "X Rank Points required" (e.g. "971").
4. Extract **Wins/Losses**: If shown (e.g. "315 Wins", "315 Losses").

---
IF HEROES_PROFILE:
1. Extract **Map Statistics**:
   - Extract Name, Games, and Win Rate (%) for EVERY map in the table.
2. Context:
   - Identify if it's "Lifetime" or a specific Season from the visual context (if any). Default to 'lifetime' if multiple seasons are likely combined.
   - viewed_hero: Detect from title (e.g. "Lt. Morales") if present.
   - is_hero_view: False.

---
IF TALENT_BUILDS:
1. Extract **Build Statistics**:
   - Extract the full Build Code (e.g. "[T3321111,LtMorales]").
   - Extract Total Games and Win Chance % for that build.
2. Context:
   - Identify the hero (e.g. "Lt. Morales").
   - Identify if it's "Lifetime" or a specific Season.
   - is_hero_view: False.

---
IF PROFILE PAGE:
1. Context:
   - is_hero_view: MANDATORY. Boolean. True if the screen shows a large hero model.
   - viewed_hero: The name of the hero shown.
   - Stat Type: EXTREMELY CRITICAL. Look at the dropdown menu in the top right of the Statistics panel. It will say "Lifetime", "2025 Season 3", "2024 Season 2", etc. Map these to "lifetime" or "season".
   - Current Rank: e.g., "Silver 5".

2. Statistics Panel (Right Side):
   - Win Rate / Winning Percent: EXACT number (e.g., 52.6%).
   - Games Played: Number.
   - KDA Ratio: Number.
   - Career Takedowns: Number.
   - Average Takedowns: Number.
   - CRITICAL: If is_hero_view is True, these stats belong to the viewed_hero.
   - If is_hero_view is False, these are GLOBAL account stats.

3. Map Statistics (CENTER TABLE):
   - Locate the table titled "MAP RECORD" in the horizontal center of the screen.
   - Extract EVERY row. This is MISSION CRITICAL.
   - For each map, capture: Name, Wins (W), Losses (L), and Win Rate (%).
   - Verify: (Wins + Losses) should be consistent with the Win Rate %.

4. Hero Statistics (Left Column):
   - Locate the list titled "MOST WINS AS" on the left (or if in a hero-specific view, use the hero context).
   - Extract Name, Level (if shown), and Games or Win Rate.

5. Role Distribution (Bar Graph at bottom right):
   - Use the EXACT numbers shown below each icon.
   - Verify: The sum of these roles MUST equal Total Games.

Return ONLY a JSON object:
{
  "screen_type": "profile_page" | "victory_screen" | "heroes_profile" | "talent_builds" | "ranked_lobby",
  "rank": "<string>",
  "rank_points": <number or null>,
  "points_required_for_promotion": <number or null>,
  "stat_type": "lifetime" | "season" (default 'season' for victory),
  "is_hero_view": <boolean>,
  "viewed_hero": "<string>",
  "player_level": <number>,
  "total_games": <number>,
  "wins": <number>,
  "losses": <number>,
  "win_rate": <number>,
  "kda_ratio": <number>,
  "avg_takedowns": <number>,
  "maps": [],
  "heroes": [],
  "roles": {},
  "talent_builds": [ {"build": "<code>", "games": <n>, "wr": <n>} ],
  "takedowns": <number>,
  "mvp_awards": <number>,
  "years_playing": <number>
}

CRITICAL: 
- For Victory Screen, map the 'Rank' to the 'rank' field and 'Rank Points' to 'rank_points'.
- For Ranked Lobby, extract both 'rank_points' (current) and 'points_required_for_promotion' (required for next rank).
"""
        
        # Call Gemini Vision API using more robust model for OCR/Vision
        # gemini-2.5-flash is the current high-tier link
        response_text = call_gemini_api(prompt, image_data=image_data, silent=True, model_override="gemini-2.5-flash", raw_mode=True)
        
        # Robust JSON Extraction
        try:
            # Try to find JSON block with regex first (handles preamble/postamble)
            import re
            json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                json_text = response_text.strip()
            
            stats = json.loads(json_text)
            
            # Mission Critical Logging
            RANK = stats.get('rank', 'N/A')
            POINTS = stats.get('rank_points', 'N/A')
            TYPE = stats.get('screen_type', 'unknown')
            
            ColoredLogger.signal("VISION", f"Scanned {TYPE}: {RANK} ({POINTS} pts)")
            print(f"--- EXTRACTED STATS ---")
            print(json.dumps(stats, indent=2))
            print(f"-----------------------")
            
            return jsonify({"success": True, "stats": stats})
            
        except (json.JSONDecodeError, AttributeError) as e:
            ColoredLogger.error(f"AI Response was not valid JSON: {e}", "VISION")
            print(f"--- RAW RESPONSE --- \n{response_text}\n--------------------")
            return jsonify({
                "success": False, 
                "error": "AI failed to format JSON correctly. Check console for raw output.",
                "raw": response_text
            }), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/verify_stats', methods=['POST'])
def verify_stats():
    """Save enriched verified stats to player profile (SQL-backed)"""
    try:
        data = request.json
        stats = data.get('stats', {})
        stat_type = data.get('stat_type', 'season')
        hero_stats = data.get('hero_stats', [])
        
        # Load profile from SQL
        profile = DB.get_kv('player_profile') or {}
        
        timestamp = datetime.now().isoformat()
        
        # 1. Update Core Profile Metadata
        if stats.get("player_level"):
            profile["player_level"] = stats["player_level"]
        if stats.get("rank"):
            profile["current_rank"] = stats["rank"]
        if stats.get("rank_points"):
             profile["rank_points"] = stats["rank_points"]
             profile["rank_updated"] = timestamp
        if stats.get("points_required_for_promotion"):
            profile["points_required_for_promotion"] = stats["points_required_for_promotion"]
            # Calculate promotion progress
            if profile.get("rank_points") and stats.get("points_required_for_promotion"):
                current = profile["rank_points"]
                required = stats["points_required_for_promotion"]
                profile["promotion_progress"] = min(100, max(0, (current / required) * 100))
                profile["points_needed"] = max(0, required - current)
        
        # 2. Update Role Distribution (Bar Graph)
        if stats.get("roles"):
            profile["role_distribution"] = stats["roles"]
            profile["role_distribution_last_verified"] = timestamp

        # 3. Update Statistics & Awards
        if "career_stats" not in profile:
            profile["career_stats"] = {}
        
        for field in ["takedowns", "mvp_awards", "years_playing"]:
            if stats.get(field):
                profile["career_stats"][field] = stats[field]

        # 4. Update Win/Loss Totals
        if "rank_data" not in profile:
            profile["rank_data"] = {}
        if "storm_league" not in profile["rank_data"]:
            profile["rank_data"]["storm_league"] = {}
            
        if stats.get("total_games") and int(stats["total_games"]) > 0:
            key = "verified_lifetime" if stat_type == 'lifetime' else "verified_season_2025_3"
            # If it's a profile page/victory screen, it's the main source
            if stats.get('screen_type') in ['profile_page', 'victory_screen']:
                profile["rank_data"]["storm_league"][key] = {
                    "total_games": int(stats["total_games"]),
                    "wins": int(stats.get("wins", 0)),
                    "losses": int(stats.get("losses", 0)),
                    "win_rate": float(stats.get("win_rate", 0)),
                    "last_verified": timestamp
                }
                profile["rank_data"]["last_updated"] = timestamp
                profile["rank_data"]["source"] = f"Full Profile Screen ({datetime.now().strftime('%Y-%m-%d')})"
        
        # 5. Update Hero Stats (Context-Aware)
        # 5. Update Hero Stats (Context-Aware)
        def normalize_hero_name(name):
            """Normalize hero name to canonical Title Case format"""
            if not name:
                return name
            
            # Alias mapping for internal IDs
            HERO_ALIASES = {
                "Crusader": "Johanna", "FaerieDragon": "Brightwing", "DemonHunter": "Valla",
                "Monk": "Kharazim", "Medic": "Lt. Morales", "Firebat": "Blaze",
                "Amazon": "Cassia", "Necromancer": "Xul", "WitchDoctor": "Nazeebo",
                "Barbarian": "Sonya", "Wizard": "Li-Ming", "L90ETC": "E.T.C.",
                "Tinker": "Gazlowe", "Dryad": "Lunara", "Dreadlord": "Mal'Ganis", "LiLi": "Li Li"
            }
            
            # Special cases for proper formatting
            SPECIAL_CASES = {
                "e.t.c.": "E.T.C.",
                "lt. morales": "Lt. Morales",
                "sgt. hammer": "Sgt. Hammer",
                "li li": "Li Li",
                "li-ming": "Li-Ming",
                "cho'gall": "Cho'gall",
                "mal'ganis": "Mal'Ganis",
                "kael'thas": "Kael'thas",
                "anub'arak": "Anub'arak",
                "zul'jin": "Zul'jin"
            }
            
            # Check alias first
            if name in HERO_ALIASES:
                return HERO_ALIASES[name]
            
            # Check special cases (case-insensitive)
            name_lower = name.lower()
            if name_lower in SPECIAL_CASES:
                return SPECIAL_CASES[name_lower]
            
            # Default to Title Case
            return name.title()

        if "hero_stats" not in profile:
            profile["hero_stats"] = {}

        # 5a. General Hero List (From "Most Wins As")
        if hero_stats:
            for hs in hero_stats:
                raw_h = hs.get("hero")
                if raw_h:
                    h = normalize_hero_name(raw_h)
                    
                    if h not in profile["hero_stats"]: profile["hero_stats"][h] = {}
                    h_key = "verified_lifetime" if stat_type == 'lifetime' else "verified_season_2025_3"
                    
                    # Merge existing
                    if h_key not in profile["hero_stats"][h]: profile["hero_stats"][h][h_key] = {}
                    
                    profile["hero_stats"][h][h_key].update({
                        "level": hs.get("level"),
                        "games": hs.get("games"),
                        "wr": hs.get("wr"),
                        "last_verified": timestamp
                    })

        # 5b. Focused Hero Stats (Heroes Profile / Talent Builds)
        viewed_hero = stats.get('viewed_hero')
        if viewed_hero:
            h = normalize_hero_name(viewed_hero)
            if h not in profile["hero_stats"]: profile["hero_stats"][h] = {}
            
            screen_type = stats.get('screen_type', 'profile_page')
            
            # IF SCREEN IS THIRD-PARTY (Heroes Profile / Build Site)
            if screen_type in ['heroes_profile', 'talent_builds']:
                if 'external_intelligence' not in profile["hero_stats"][h]:
                    profile["hero_stats"][h]['external_intelligence'] = {}
                
                ext = profile["hero_stats"][h]['external_intelligence']
                ext_key = "season_3" if stat_type != 'lifetime' else "lifetime" # Simplification for external data

                # Save Maps
                if stats.get('maps'):
                    # Merge logic could go here, for now overwrite list to avoid dupes
                    if 'map_stats' not in ext: ext['map_stats'] = []
                    # Append or Replace? Let's Append unique maps for now or just replace to avoid "wonkiness"
                    ext['map_stats'] = stats.get('maps') 
                    ext['last_verified'] = timestamp
                    ext['source_maps'] = f"Heroes Profile ({datetime.now().strftime('%Y-%m-%d')})"

                # Save Builds
                if stats.get('talent_builds'):
                    ext['talent_builds'] = stats.get('talent_builds')
                    ext['last_verified'] = timestamp
                    ext['source_builds'] = f"Heroes Profile ({datetime.now().strftime('%Y-%m-%d')})"

            # IF SCREEN IS IN-GAME PROFILE (Official Blizzard Stats)
            else:
                h_key = "verified_lifetime" if stat_type == 'lifetime' else "verified_season_2025_3"
                if h_key not in profile["hero_stats"][h]: profile["hero_stats"][h][h_key] = {}

                # Save basic stats if valid numbers exist (often null in these specific views)
                if stats.get('win_rate') is not None:
                    profile["hero_stats"][h][h_key]['wr'] = stats.get('win_rate')
                if stats.get('total_games') is not None:
                    profile["hero_stats"][h][h_key]['games'] = stats.get('total_games')
        
        # 6. Update Map Records
        if stats.get("maps"):
            if "map_records_verified" not in profile:
                profile["map_records_verified"] = {}
            for mr in stats["maps"]:
                map_name = mr.get("map")
                if map_name:
                    profile["map_records_verified"][map_name] = {
                        "wins": mr.get("wins"),
                        "losses": mr.get("losses"),
                        "win_rate": mr.get("wr"),
                        "last_verified": timestamp
                    }

        # Save profile back to SQL
        DB.set_kv('player_profile', profile)
        
        # Reload Context Cache to propagate changes to AI
        CACHE.load_all()
        
        ColoredLogger.success(f"Verified stats synchronized to SQLite (Type: {stat_type})", "API")
        
        # Update blizzard_verified.json source for Data Provenance tracking
        sources_dir = "src/data/sources"
        os.makedirs(sources_dir, exist_ok=True)
        blizzard_source_path = os.path.join(sources_dir, "blizzard_verified.json")
        
        try:
            with open(blizzard_source_path, 'r') as f:
                blizzard_source = json.load(f)
        except:
            blizzard_source = {"verifications": []}
        
        # Add this verification to the source log
        verification_entry = {
            "timestamp": timestamp,
            "stat_type": stat_type,
            "total_games": stats.get("total_games"),
            "hero_stats": hero_stats or [],
            "maps": stats.get("maps", []),
            "method": "screenshot_ui_enriched"
        }
        
        blizzard_source.setdefault("verifications", []).insert(0, verification_entry)
        
        # Keep only last 50 verifications
        blizzard_source["verifications"] = blizzard_source["verifications"][:50]
        
        with open(blizzard_source_path, 'w') as f:
            json.dump(blizzard_source, f, indent=2)
        
        from scripts.ingestion_logger import log_blizzard_verification
        log_blizzard_verification(stats=stats, method="screenshot_ui_enriched")
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('API_PORT', 5001))
    # ColoredLogger.success(f"Cerebrate API Online | Port: {port}", "API")  # Redundant - shown in banner
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        ColoredLogger.info("🛑 API server stopped", "API")
    except Exception as e:
        ColoredLogger.error(f"Server error: {e}", "API")
