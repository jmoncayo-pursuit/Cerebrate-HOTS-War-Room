# Grandmaster Telemetry & Forensic Analysis Plan

## 🎯 Objective
Transition Cerebrate from "Statistical Inference" (guessing intent) to "Forensic Telemetry" (proving intent). We will bridge the remaining data gaps in the Heroes of the Storm replay parsing engine to achieve a "Grandmaster" standard of match analysis.

## 🔍 The 4 Core Data Gaps

### 1. Target Focus Frequency ("The Who")
*   **Source**: `NNet.Replay.Game.SCmdEvent` (Command clicks) + `NNet.Replay.Tracker.SUnitPositionsEvent` (Unit locations).
*   **Implementation**: Cross-reference player Right-Clicks (TargetPoint) with enemy unit coordinates at the exact timestamp.
*   **Result**: Calculate "Target Stickiness" and "Click Accuracy." Prove if the player was focusing tanks or backline squishies.

### 2. Over-Extension & Safe-Zone Telemetry
*   **Source**: `NNet.Replay.Tracker.SUnitPositionsEvent` ($x, y$ coordinates).
*   **Implementation**: Calculate the distance between the player and their nearest ally (Frontline/Tank) during teamfight windows.
*   **Result**: Quantitative "Over-extension Coefficient." Move from "You died outnumbered" to "You were 32 units away from safety during the engage."

### 3. Granular CC Effectiveness
*   **Source**: `NNet.Replay.Tracker.SScoreResultEvent` (`TimeStunningEnemyHeroes`, `TimeRootingEnemyHeroes`, etc.).
*   **Implementation**: Extract individual CC types instead of an aggregated "CC Time."
*   **Result**: "Impact Distribution" analysis. Evaluate if CC was used to peel or to secure terminal kills.

### 4. Positional Healing Allocation
*   **Source**: Healer $(x, y)$ Position vs. Ally Health Deficits.
*   **Implementation**: Analyze if the healer was physically close to the ally with the highest health deficit during deaths.
*   **Result**: Prove "Positional Neglect" or "Priority Misalignment."

---

## 🛠️ Execution Phases

### Phase 1: Telemetry Parser Upgrade
- [ ] Modify `replay_parser.py` to decode `SUnitPositionsEvent`.
- [ ] Implement sampling logic (extract positions every 5 seconds to manage file size).
- [ ] Extract granular CC stats from `SScoreResultEvent`.

### Phase 2: Behavioral Analysis Engine
- [ ] Create logic to calculate "Distance from Team" during death events.
- [ ] Implement "Kill Participation Heatmaps" (conceptualizing where kills occur).

### Phase 3: AI Prompt & Gold Standard Synchronization
- [ ] Update `api_server.py` to handle the new telemetry fields.
- [ ] Update `GOLD_STANDARDS.md` with positioning-aware analysis examples.
- [ ] Perform a full incremental re-parse of all 109 matches.

---

## ✅ Current Progress (Pre-Commit)
1.  **Forensic Death Logs**: Parser now tracks `killer_pid` for every hero death.
2.  **Pseudo-Hero Filtering**: Filtered out Molten Core, Vehicles, and Summons from death counts to prevent "False Deaths."
3.  **Gold Standard v2**: Updated the reference matches with MM:SS timestamps and specific killer/victim citations.
4.  **Incremental Reparse**: Added `death_events` strategy to update existing history.

---
*Documented by Cerebrate AI - 2026-01-05*
