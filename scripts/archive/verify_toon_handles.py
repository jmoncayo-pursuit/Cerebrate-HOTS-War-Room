
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.services.database import DatabaseManager
import json

db = DatabaseManager()
matches = db.get_matches(limit=5)
for m in matches:
    print(f"Match {m['id']}")
    for p in m.get('players', []):
        print(f"  {p.get('name')}: {p.get('toon_handle')}")
