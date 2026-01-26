import sqlite3
import json

db_path = "/Users/jmoncayopursuit.org/Desktop/Cerebrate-HOTS-War-Room/src/data/cerebrate.db"
conn = sqlite3.connect(db_path)

analysis = {
    "verdict": "Macro Engine",
    "summary": "STRATEGIC RESOURCE TRADE. On Alterac Pass, you maintained a constant pressure anchor with 7,317 Minion XP. The deaths at 4:10, 8:43, 11:05, and 13:19 represent a high-attrition trade: attracting multiple enemy resources (Chromie/Imperius) to off-lanes. While tactical coordination was absent during these intervals, the resulting 15:39 victory confirms that the Lane Pressure provided the structural buffer required for the win. You functioned as the map's primary engine for level security.",
    "key_insights": {
        "kill_streak": "0",
        "mercenary_camps": "2",
        "downtime": "1:20",
        "minion_xp": "7317"
    },
    "critical_mistake": "Attrition Limit: Exposure during isolated lane soaking attracted 25% of total enemy deaths to your position. No further tactical failure identified.",
    "win_condition": "Macro Supremacy: Secured a 15:39 victory through consistent structural pressure and XP anchoring.",
    "tactical_breakdown": "Neural Priority: High. Secured 7.3k Minion XP. Tactical decision-making was independent of team rotation cadence, resulting in high-attrition resource trades."
}

conn.execute("UPDATE matches SET analysis_json = ? WHERE id = ?", (json.dumps(analysis), "96d633f81151e214"))
conn.commit()
conn.close()
print("Success")
