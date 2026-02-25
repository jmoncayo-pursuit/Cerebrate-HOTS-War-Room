import json
import os
from datetime import datetime
from api.services.database import DatabaseManager

class AgenticBrain:
    def __init__(self):
        # Use the correct DatabaseManager that works with nexus_command_lab.db
        self.db = DatabaseManager()
        self.map_names = [
            "Alterac Pass", "Battlefield of Eternity", "Blackheart's Bay", 
            "Braxis Holdout", "Cursed Hollow", "Dragon Shire", 
            "Garden of Terror", "Hanamura Temple", "Infernal Shrines", 
            "Sky Temple", "Tomb of the Spider Queen", "Towers of Doom", 
            "Volskaya Foundry", "Warhead Junction"
        ]

    def process_request(self, message, image_data=None):
        """
        Execute an agentic audit before generating a response.
        """
        message_low = message.lower()
        
        # 1. IDENTIFY TACTICAL TARGETS
        detected_map = self._detect_map(message_low)
        detected_hero = self._detect_hero(message_low)
        
        # 2. PERFORM AGENTIC AUDIT (SQL QUERY PHASE)
        audit_data = {
            "map_context": None,
            "hero_context": None,
            "social_intelligence": None,
            "global_meta": None,
            "constraints": self._get_constraints()
        }
        
        if detected_map:
            audit_data["map_context"] = self._audit_map(detected_map)
            
        if detected_hero:
            audit_data["hero_context"] = self._audit_hero(detected_hero, detected_map)
            
        # 3. SYNTHESIZE Dossier
        dossier = self._build_tactical_dossier(audit_data, detected_map, detected_hero)
        
        return dossier

    def _detect_map(self, text):
        for m in self.map_names:
            if m.lower() in text:
                return m
        return None

    def _detect_hero(self, text):
        # We could pull all hero names from DB to be precise
        with self.db._get_connection() as conn:
            heroes = conn.execute("SELECT hero FROM global_meta_stats").fetchall()
            for h in heroes:
                name = h['hero']
                if name.lower() in text and len(name) > 3:
                    return name
        return None

    def _get_hero_role(self, hero_name):
        config = self.db.get_kv('hero_roles') or {}
        for role, heroes in config.items():
            if hero_name in heroes:
                return role
        return "Ranged Assassin" # Default fallback

    def _get_constraints(self):
        config = self.db.get_kv('cerebrate_config') or {}
        return config.get('roster_constraints', {})

    def _audit_map(self, map_name):
        """Perform a deep SQL audit for a specific map, merging map-stats with lifetime mastery."""
        with self.db._get_connection() as conn:
            # 1. Fetch Lifetime Mastery for all played heroes (excluding dislikes if possible, but we'll filter later)
            mastery = conn.execute('''
                SELECT hero, win_rate, games_played as games
                FROM global_meta_stats 
                WHERE games_played > 0
                ORDER BY games_played DESC
            ''').fetchall()
            
            # 2. Fetch Map-Specific stats
            map_stats = conn.execute('''
                SELECT hero, COUNT(*) as games, SUM(CASE WHEN result='WIN' THEN 1 ELSE 0 END) as wins
                FROM matches 
                WHERE map = ? 
                GROUP BY hero
            ''', (map_name,)).fetchall()
            
            # Map stats lookup
            m_lookup = {r['hero']: {'games': r['games'], 'wins': r['wins']} for r in map_stats}
            
            # 3. Fetch Role Mapping
            config = self.db.get_kv('hero_roles') or {}
            hero_to_role = {}
            for role, heroes in config.items():
                for h in heroes:
                    hero_to_role[h] = role

            # 4. Synthesize Mastery Assets
            assets = []
            for m in mastery:
                h = m['hero']
                ms = m_lookup.get(h, {'games': 0, 'wins': 0})
                
                # Calculate a "Tactical Weight"
                # Priority: Map Performance (if > 3 games) -> Lifetime Mastery
                display_wr = m['win_rate']
                if ms['games'] >= 3:
                     display_wr = round((ms['wins'] / ms['games']) * 100, 1)

                assets.append({
                    "hero": h,
                    "role": hero_to_role.get(h, "Assassin"),
                    "lifetime_games": m['games'],
                    "lifetime_wr": m['win_rate'],
                    "map_games": ms['games'],
                    "map_wr": display_wr,
                    "is_verified": ms['games'] >= 3
                })
            
            # 5. Get Recent History for Context
            recent = conn.execute('''
                SELECT hero, result, date FROM matches 
                WHERE map = ? 
                ORDER BY date DESC LIMIT 3
            ''', (map_name,)).fetchall()
            
            return {
                "all_assets": assets,
                "recent_history": [dict(r) for r in recent]
            }

    def _audit_hero(self, hero_name, map_name=None):
        """Perform a deep SQL audit for a specific hero."""
        with self.db._get_connection() as conn:
            # Lifetime stats
            lifetime = conn.execute('''
                SELECT win_rate, games_played, avg_level as level
                FROM global_meta_stats WHERE hero = ?
            ''', (hero_name,)).fetchone()
            
            if lifetime:
                l = dict(lifetime)
                l['wins'] = round((l['win_rate'] / 100) * l['games_played'])
                l['losses'] = l['games_played'] - l['wins']
                lifetime = l
            
            # Map specific if provided
            map_stats = None
            if map_name:
                map_stats = conn.execute('''
                    SELECT COUNT(*) as games, SUM(CASE WHEN result='WIN' THEN 1 ELSE 0 END) as wins
                    FROM matches WHERE hero = ? AND map = ?
                ''', (hero_name, map_name)).fetchone()
                
            # Best builds
            builds = self.db.get_top_builds(hero_name, limit=2)
            
            # Lethality Correlation
            lethality = self._audit_lethality(hero_name)
            
            return {
                "lifetime": dict(lifetime) if lifetime else None,
                "map_stats": dict(map_stats) if map_stats else None,
                "top_builds": builds,
                "lethality": lethality
            }

    def _audit_lethality(self, hero_name):
        """Analyze win rate correlation with kill thresholds."""
        with self.db._get_connection() as conn:
            # Query all matches for this hero and process in Python for robustness
            games = conn.execute('''
                SELECT m.result, p.stats
                FROM match_players p JOIN matches m ON p.match_id = m.id
                WHERE p.hero = ?
            ''', (hero_name,)).fetchall()
            
            high_wins = 0
            high_games = 0
            low_wins = 0
            low_games = 0
            
            for g in games:
                try:
                    stats = json.loads(g['stats'])
                    kills = stats.get('SoloKill', 0)
                    is_win = 'WIN' in g['result'].upper() or 'VICTORY' in g['result'].upper()
                    if kills >= 5:
                        high_games += 1
                        if is_win: high_wins += 1
                    else:
                        low_games += 1
                        if is_win: low_wins += 1
                except: continue
                
            high_wr = round((high_wins / high_games * 100), 1) if high_games > 0 else 0
            low_wr = round((low_wins / low_games * 100), 1) if low_games > 0 else 0
            
            return {
                "high": {"games": high_games, "wins": high_wins, "wr": high_wr},
                "low": {"games": low_games, "wins": low_wins, "wr": low_wr},
                "threshold": 5
            }

    def _build_tactical_dossier(self, audit, map_name, hero_name):
        """Construct the raw intelligence payload for the AI."""
        dossier = "=== AGENTIC TACTICAL DOSSIER [SOURCE: HYBRID_SYNTHESIS] ===\n"
        dossier += "METADATA: All stats marked 'Verified' pull directly from SECURE_DATALINK (SQL Archive).\n"
        dossier += "METADATA: Strategic directives are generated via NEURAL_SYNTHESIS (Cross-referenced analysis).\n\n"
        
        # Freshness Check: Load Rework Registry
        rework_path = os.path.join(os.path.dirname(__file__), '..', '.agent', 'brain', 'REWORK_REGISTRY.md')
        if os.path.exists(rework_path):
            with open(rework_path, 'r') as f:
                dossier += f"⚠️ REWORK REGISTRY (DO NOT RECOMMEND STALE SPECS FOR THESE HEROES):\n{f.read()}\n\n"

        # Constraints and exclusions
        constraints = audit.get("constraints", {})
        excluded = set(constraints.get('global_bans', []))

        if map_name:
            dossier += f"MAP CONTEXT: {map_name.upper()}\n"
            assets = audit.get("map_context", {}).get("all_assets", [])
            
            if not assets:
                dossier += "⚠️ CRITICAL: NO USER DATA FOUND. REQUEST GLOBAL META FALLBACK.\n"
            
            # Roles for structured output
            roles = ["Bruiser", "Healer", "Tank", "Ranged Assassin"]

            for role in roles:
                # Filter by role and exclude dislikes
                role_assets = [a for a in assets if a['role'] == role and a['hero'] not in excluded]
                
                # Scoring Algorithm: Prioritize Map Performance (if verified) > Lifetime Mastery
                # Score = (MapWR if Verified else 0) + (LifetimeGames / 100) + (LifetimeWR / 10)
                def get_score(a):
                    score = (a['lifetime_wr'] / 10) + (a['lifetime_games'] / 100)
                    if a['is_verified']:
                        # Verified map stats are a massive multiplier
                        score += 500 + (a['map_wr'] * 2)
                    return score
                
                sorted_role = sorted(role_assets, key=get_score, reverse=True)[:2]
                
                if sorted_role:
                    dossier += f"\n[{role.upper()}]\n"
                    for a in sorted_role:
                        source = f"Verified {a['map_wr']}% WR" if a['is_verified'] else f"Lifetime Mastery"
                        dossier += f"- {a['hero']}: {a['map_wr']}% WR | {a['lifetime_games']} games total ({source})\n"
            
            if audit.get("recent_history"):
                hist = ", ".join([f"{r['hero']} ({r['result']})" for r in audit["recent_history"]])
                dossier += f"\nRECENT MISSION HISTORY: {hist}\n"
        
        if hero_name:
            dossier += f"\nTARGET HERO INTEL: {hero_name}\n"
            h_ctx = audit.get("hero_context", {})
            if h_ctx.get("lifetime"):
                l = h_ctx["lifetime"]
                dossier += f"- Service Record: {l.get('wins', 0)}W-{l.get('losses', 0)}L ({l.get('win_rate', 0)}% Effectiveness)\n"
            if h_ctx.get("top_builds"):
                b = h_ctx["top_builds"][0]
                dossier += f"- Neural link (Draft Optima): {b['build_code']} ({b['win_rate']}% WR)\n"
            if h_ctx.get("lethality"):
                leth = h_ctx["lethality"]
                if leth['high']['games'] > 0:
                    dossier += f"\n[LETHALITY THRESHOLD ANALYSIS]\n"
                    dossier += f"- {leth['threshold']}+ Kills: {leth['high']['wr']}% WR ({leth['high']['wins']}/{leth['high']['games']})\n"
                    dossier += f"- Under {leth['threshold']} Kills: {leth['low']['wr']}% WR ({leth['low']['wins']}/{leth['low']['games']})\n"
                    if leth['high']['wr'] > leth['low']['wr'] + 15:
                        dossier += f"⚠️ STRATEGIC DISCOVERY: Crossing the {leth['threshold']} kill threshold is a primary Victory Condition (+{round(leth['high']['wr']-leth['low']['wr'])}% jump).\n"
        
        if constraints.get('global_bans'):
            dossier += f"\n⚠️ BLACKLISTED ASSETS (Manual Override): {', '.join(constraints['global_bans'])}\n"
            
        dossier += "\nTACTICAL DIRECTIVE: Prioritize 'Verified' assets for optimal mission success. Use 'Neural' insights for high-variance situational adaptations.\n"
        if map_name and not hero_name:
             dossier += "TACTICAL DIRECTIVE: User has NOT selected a hero yet. Suggest the best heroes from the list above for this map and explain WHY they are good picks (macro, objective control, etc). DO NOT give tips on how to fight with specific heroes unless asked.\n"
        dossier += "========================================================\n"
        return dossier

    def get_draft_recommendations(self, map_name):
        """Returns structured JSON recommendations for the Draft Simulator."""
        audit = self._audit_map(map_name)
        assets = audit.get("all_assets", [])
        
        # Scoring Algorithm matching _build_tactical_dossier
        def get_score(a):
            score = (a['lifetime_wr'] / 10) + (a['lifetime_games'] / 100)
            if a['is_verified']:
                score += 500 + (a['map_wr'] * 2)
            return score

        recommendations = []
        roles = ["Tank", "Healer", "Bruiser", "Ranged Assassin"]
        
        # Get one top pick per major role for the vision panel
        for role in roles:
            role_assets = [a for a in assets if a['role'] == role]
            if not role_assets: continue
            
            top_pick = sorted(role_assets, key=get_score, reverse=True)[0]
            
            # Simple tactic generation
            tactic = f"High performance on {map_name}."
            if top_pick['is_verified']:
                tactic = f"Verified {top_pick['map_wr']}% win rate on this map archive."
            elif top_pick['lifetime_wr'] > 55:
                tactic = f"Exceptional lifetime mastery ({top_pick['lifetime_wr']}% WR)."

            recommendations.append({
                "hero": top_pick['hero'],
                "role": role,
                "win_rate": top_pick['map_wr'] if top_pick['is_verified'] else top_pick['lifetime_wr'],
                "is_verified": top_pick['is_verified'],
                "tactic": tactic,
                "label": "Optimal Pick" if top_pick['is_verified'] else "Mastery Pick"
            })
            
        return {
            "map": map_name,
            "recommendations": recommendations[:3], # Return top 3 for the UI
            "confidence": 95 if any(r['is_verified'] for r in recommendations) else 75
        }
