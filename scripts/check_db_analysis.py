import sqlite3
import json
import os

DB_PATH = "/Users/jmoncayopursuit.org/Desktop/Cerebrate-HOTS-War-Room/war_room.db"

def check_analysis():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("Checking last 10 matches for analysis status...")
    cursor.execute("SELECT id, hero, map, analysis FROM matches ORDER BY date DESC LIMIT 10")
    rows = cursor.fetchall()
    
    for row in rows:
        has_analysis = bool(row['analysis'] and row['analysis'] != '{}' and row['analysis'] != 'null')
        analysis_preview = ""
        if has_analysis:
            try:
                data = json.loads(row['analysis'])
                analysis_preview = f"Verdict: {data.get('verdict', 'N/A')}"
            except:
                analysis_preview = "Invalid JSON"
        
        print(f"ID: {row['id']} | Hero: {row['hero']} | Map: {row['map']} | Analyzed: {has_analysis} | {analysis_preview}")
    
    conn.close()

if __name__ == "__main__":
    check_analysis()
