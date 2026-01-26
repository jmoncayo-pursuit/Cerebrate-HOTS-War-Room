import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_manager import DatabaseManager
import json

def main():
    print("Hydrating Repository JSONs from Database (Public Data Only)...")
    db = DatabaseManager()
    
    # Map of DB Key -> Filename
    # Only export SHARED/PUBLIC data. Personal data stays in DB/ignored.
    export_map = {
        'talents': 'talents.json',
        'hero_patches': 'hero_patches.json',
        'hero_data': 'hero_data.json',
        'talent_id_map': 'talent_id_map.json',
        'hero_roles': 'hero_roles.json',
        'global_meta_stats': 'global_stats_dump.json' # Special case table
    }
    
    for key, filename in export_map.items():
        data = None
        if key == 'global_meta_stats':
            # Dump table
            with db._get_connection() as conn:
                rows = conn.execute("SELECT * FROM global_meta_stats").fetchall()
                data = [dict(r) for r in rows]
                # If we dump this, we should consider if it's too big/personal. 
                # Global stats are usually non-personal.
        else:
            data = db.get_kv(key)
            
        if data:
            path = os.path.join('src', 'data', filename)
            with open(path, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"✅ Exported {key} -> {path} ({len(data)} records)")
        else:
            print(f"⚠️  Skipping {key}: No data found in DB.")

if __name__ == "__main__":
    main()
