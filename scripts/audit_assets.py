import sqlite3
import os

db_path = 'war_room.db'
images_dir = 'public/images/heroes'
maps_dir = 'public/images/maps'

def normalize(name):
    # Match the JS logic roughly
    name = name.lower().strip()
    special = {
        "the butcher": "thebutcher",
        "sgt. hammer": "sgthammer",
        "lt. morales": "ltmorales",
        "d.va": "dva",
        "e.t.c.": "etc",
        "anub'arak": "anubarak",
        "kael'thas": "kaelthas",
        "kel'thuzad": "kelthuzad",
        "zul'jin": "zuljin",
        "gul'dan": "guldan",
        "mal'ganis": "malganis",
        "li li": "lili",
        "li-ming": "liming",
        "cho'gall": "cho"
    }
    if name in special: return special[name]
    return "".join(c for c in name if c.isalnum())

def audit():
    conn = sqlite3.connect(db_path)
    heroes = [r[0] for r in conn.execute("SELECT hero FROM hero_stats").fetchall()]
    matches = [r[0] for r in conn.execute("SELECT DISTINCT map FROM matches").fetchall()]
    conn.close()

    print(f"--- HERO ICON AUDIT ({len(heroes)} heroes) ---")
    missing_heroes = []
    for h in heroes:
        norm = normalize(h)
        path = os.path.join(images_dir, f"{norm}.png")
        if not os.path.exists(path):
            missing_heroes.append((h, norm))
    
    if missing_heroes:
        for m in missing_heroes:
            print(f"MISSING: {m[0]} (expected {m[1]}.png)")
    else:
        print("All hero icons accounted for.")

    print(f"\n--- MAP ICON AUDIT ({len(matches)} maps) ---")
    # Map normalization logic is different in JS, but let's check basic slugs
    for m in matches:
        if not m: continue
        norm = m.lower().replace(" ", "-").replace("'", "")
        path = os.path.join(maps_dir, f"{norm}.png")
        if not os.path.exists(path):
             # Try common variations
             found = False
             for f in os.listdir(maps_dir):
                 if norm in f:
                     found = True
                     break
             if not found:
                 print(f"MISSING MAP: {m} (tried {norm}.png)")
        else:
            print(f"OK: {m}")

if __name__ == "__main__":
    audit()
