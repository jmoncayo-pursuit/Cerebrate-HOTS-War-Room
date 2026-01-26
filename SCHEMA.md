# 🗄️ Cerebrate Database Schema

This document outlines the structure of the `cerebrate.db` SQLite database. This schema is used by the Cerebrate War Room to track match history, player performance, and AI-generated insights.

---

## **PRIMARY TABLES**

### **`matches`**
The main table for game metadata and high-level results.
- `id` (TEXT, PK): Unique match identifier.
- `map` (TEXT): The name of the map.
- `result` (TEXT): "WIN" or "LOSS".
- `hero` (TEXT): The hero played by the user.
- `date` (TEXT): ISO timestamp of the match.
- `game_length` (INTEGER): Duration in seconds.
- `talent_build` (TEXT): Your specific build code (e.g., `T1232213`).
- `analysis_json` (TEXT): Detailed AI analysis from the Gemini Swarm.
- `advanced_stats_json` (TEXT): Complex metrics (healing, damage, etc.).

### **`match_players`**
Drill-down table for every player in every match.
- `match_id` (TEXT): Link to the `matches` table.
- `name` (TEXT): BattleTag or Player Name.
- `hero` (TEXT): Hero played by this specific player.
- `team` (INTEGER): 0 or 1.
- `winner` (BOOLEAN): 1 for win, 0 for loss.
- `stats_json` (TEXT): Raw hero performance metrics.
- `talents_json` (TEXT): List of talents picked and timestamps (Legacy).
- `banking_ledger_json` (TEXT): Economy data (Gems, Coins, Warheads).

### **`match_player_talents`**
Flattened talent choices for every player in every match. Used for deep statistical analysis of build performance.
- `match_id` (TEXT): Link to the `matches` table.
- `player_name` (TEXT): Name of the player.
- `hero` (TEXT): Hero name.
- `level` (INTEGER): The level tier of the talent (1, 4, 7, 10, 13, 16, 20).
- `talent_id` (TEXT): Internal game ID for the talent.
- `talent_name` (TEXT): Human-readable name of the talent.

---

### **`hero_stats`**
Your cumulative performance per hero.
- `hero` (TEXT, PK): Hero name.
- `wins` / `losses` / `games_played` (INTEGER).
- `win_rate` (REAL).
- `level` (INTEGER): In-game progression.

---

## **AI REFINEMENT TABLES**

### **`summary_grades`**
Used by the **Referee Agent** to score the quality of AI match summaries.
- `strategic_accuracy` / `persona_consistency` / `map_specific_insight` (INTEGER 1-10).
- `overall_score` (REAL).

### **`gold_standard_examples`**
Few-shot learning examples for the AI to emulate high-quality writing.
- `gold_summary` (TEXT): Curated "Perfect" summary.
- `gold_verdict` (TEXT): Curated "Perfect" tactical breakdown.

---

## **PRIVACY NOTE**
The database file itself (`cerebrate.db`) is listed in `.gitignore` and is NEVER committed. Only this schema and the management code in `database_manager.py` are shared.
