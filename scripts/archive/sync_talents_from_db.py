from database_manager import DatabaseManager
import json
import os

def main():
    print("Syncing Talents from DB to File...")
    db = DatabaseManager()
    talents = db.get_kv('talents')

    if not talents or len(talents) < 5:
        print("ERROR: DB talents seem empty or invalid. Aborting sync.")
        return

    output_path = 'src/data/talents.json'
    
    with open(output_path, 'w') as f:
        json.dump(talents, f, indent=4)
        
    print(f"SUCCESS: Wrote {len(talents)} heroes' talents to {output_path}")

if __name__ == "__main__":
    main()
