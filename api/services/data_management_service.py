import os
import json
from datetime import datetime
from api.services.database import DatabaseManager

class DataManagementService:
    """Consolidated service for roster management, strategies, and data provenance."""
    
    def __init__(self, db_manager=None):
        self.db = db_manager or DatabaseManager()

    # --- ROSTER & CONSTRAINTS ---
    def get_constraints(self):
        return self.db.get_kv('cerebrate_config') or {}

    def update_hero_status(self, hero, action):
        config = self.get_constraints()
        bans = config.setdefault('roster_constraints', {}).setdefault('global_bans', [])
        if action == 'ban' and hero not in bans: bans.append(hero)
        elif action == 'unban' and hero in bans: bans.remove(hero)
        self.db.set_kv('cerebrate_config', config)
        return config

    # --- STRATEGIES ---
    def get_strategies(self, map_name=None):
        strategies = self.db.get_kv('map_strategies') or {}
        return strategies.get(map_name) if map_name else strategies

    # --- DATA PROVENANCE & CONFLICTS ---
    def get_global_meta(self):
        try:
            with self.db._get_connection() as conn:
                rows = conn.execute('SELECT * FROM global_meta_stats').fetchall()
                data = [dict(r) for r in rows]
                for hero in data:
                    hero['name'] = hero['hero']
                    if hero.get('builds_json'):
                        try:
                            hero['builds'] = json.loads(hero['builds_json'])
                        except:
                            hero['builds'] = []
                    else:
                        hero['builds'] = []
                return data
        except Exception as e:
            print(f"Error fetching global meta: {e}")
            return []

    def get_source_status(self):
        log = self.db.get_kv('ingestion_log') or {"entries": []}
        return log.get('entries', [])[:10]

    def get_data_conflicts(self):
        # Implementation from old DataService
        return []
