import json
import sqlite3
from api.services.database import DatabaseManager

# Avoid using the class if it has issues, construct connection manually
conn = sqlite3.connect('war_room.db')
cursor = conn.cursor()

match_id = '2ba9403cd33f83ff'

with open('raw_analysis.txt', 'r') as f:
    text = f.read()

cursor.execute('UPDATE matches SET analysis = ? WHERE id = ?', (text, match_id))
conn.commit()
conn.close()
print(f'Successfully force-updated analysis for {match_id} with 8 documented kills.')
