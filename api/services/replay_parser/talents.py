import os
import json
from api.logger import ColoredLogger

TALENTS_DB = None

def load_talent_data(db_manager=None):
    global TALENTS_DB
    if TALENTS_DB is not None: return
    try:
        from ..database import DatabaseManager
        db = db_manager or DatabaseManager()
        TALENTS_DB = db.get_kv('talents')
        if TALENTS_DB: return
        
        paths = ['src/data/talents.json', 'data/talents.json']
        for p in paths:
            if os.path.exists(p):
                with open(p, 'r') as f:
                    TALENTS_DB = json.load(f)
                return
        TALENTS_DB = {}
    except Exception as e:
        ColoredLogger.error(f"Error loading talents: {e}", "PARSER")
        TALENTS_DB = {}

def get_talent_from_index(hero_name, index, talent_db):
    if not talent_db or not hero_name: return None
    hero_key = None
    h_clean = hero_name.lower().replace(' ','').replace('.','').replace("'","")
    for k in talent_db.keys():
        if k.lower().replace(' ','').replace('.','').replace("'","") == h_clean:
            hero_key = k
            break
    if not hero_key:
         internal_map = {"crusader":"johanna", "amazon":"cassia", "barbarian":"sonya", "traitorhero":"varian", "necromancer":"xul", "wizard":"li-ming", "d3wizard":"li-ming", "witchdoctor":"nazeebo"}
         mapped = internal_map.get(hero_name.lower())
         if mapped:
             for k in talent_db.keys():
                if k.lower() == mapped:
                    hero_key = k
                    break
    if not hero_key: return None
    hero_talents = talent_db[hero_key]
    curr = 0
    tiers = sorted(hero_talents.keys(), key=lambda x: int(x) if x.isdigit() else 99)
    for t in tiers:
        cols = hero_talents[t]
        sorted_cols = sorted(cols.keys(), key=lambda x: int(x) if x.isdigit() else 99)
        for c in sorted_cols:
            if curr == index: return cols[c].get('tooltipId')
            curr += 1
    return None
