
# 🧠 Nexus Command Lab: Tactical Operations Center

> "The difference between victory and defeat is often a single correct decision in the draft."

**Nexus Command Lab** is an advanced tactical intelligence suite designed for Heroes of the Storm. It transforms raw match telemetry into actionable psychological and tactical advantages through multi-agent AI analysis and forensic match review.

## 🚀 Key Features

### ⚔️ Command Center
Real-time drafting intelligence. Upload a screenshot of your loading screen or draft lobby to:
- **Identify Combatants**: Scans teammates and enemies for known historical data.
- **Predict Outcomes**: Calculates win probabilities based on map-specific mastery and team compositions.
- **Social Intelligence**: Flags "Synergy Anchors" (reliable allies) and "Apex Threats" (recurring nemesis rivals).

### 🎒 The Arsenal
A categorized view of your hero pool, preventing "experimental picks" on maps where you should be playing your best:
- **Proven**: High games, high win rate. Your reliable anchors.
- **Hot Streaks**: Momentum-based picks from the current season.
- **Pockets**: Low sample size but high performance "secret weapons".
- **Untapped**: High general skill but latent map-specific potential.
- **Avoid**: Statistically confirmed weaknesses.

### 🧭 Map Directives
For every map in the rotation, Nexus Command Lab defines a specific **Win Condition** (e.g., RACE, ZONE, PUSH) and recommends heroes that excel at executing that specific strategy.

### 🤖 Multi-Agent AI System
Nexus Command Lab uses a specialized swarm of AI agents, each optimized for specific domains:
- **FORENSIC ANALYST**: Post-game forensic analysis, identifying subtle mechanical failures and critical turning points. 
- **SCOUT**: Draft intelligence, hero recommendations, ban priorities.
- **TACTICIAN**: Map-specific strategies, rotation timing, objective prioritization.
- **SOCIAL**: Player synergy analysis, nemesis tracking, duo queue recommendations.
- **AUDIT**: Quality assurance agent that verifies AI predictions against replay truth.
- **MECHANICAL**: Specialized micro-analysis for specific heroes (Stitches Hooks, Kharazim Dashes, Azmodan Stacks).

### 📊 Data Provenance
Multi-source verification ensures your stats are accurate:
- **Blizzard Source**: Official totals and rank verification via screenshot ingestion.
- **Forensic Replay Parser**: Granular talent-level data, DC detection, and teammate/enemy interaction history (v3.2).
- **Audit Logs**: Transparent history of how stats were calculated.
- **Source Attribution**: Every stat displays its source (Verified/Parsed/Baseline).

## 🧠 Cognitive Architecture
Nexus Command Lab leverages a best-in-class multi-model strategy, routing tasks to the most effective intelligence:
- **Multimodal Vision**: Identifies allies and enemies from screenshots.
- **Structured Relational RAG**: Ingests massive JSON telemetry streams into large token windows for forensic-level analysis.
- **Autonomous Swarm Intelligence**: Multi-agent system (Scout, Analyst, Tactician, etc.) for specialized recommendations.
- **Truth Validation**: Dedicated "Auditor" agent that cross-references AI narrative against hard replay data.

## 🛠️ Technology Stack
- **Frontend**: React, Vite, Tailwind CSS, Framer Motion
- **Backend**: Python (Flask), SQLite (Nexus Core)
- **AI**: Multi-model orchestration (Gemini 2.0, GPT-4o, Claude 3.5)
- **Processing**: Custom Python Replay Parser (MPQ based)

## 🚦 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Gemini API key
- Heroes of the Storm (for replay file generation)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/jmoncayo-pursuit/Nexus-Command-Lab.git
   cd Nexus-Command-Lab
   ```

2. Run the unifying dev script:
   ```bash
   chmod +x dev.sh
   ./dev.sh
   ```

3. Configure your `.env` file with your Gemini API key:
   ```env
   GOOGLE_API_KEY=your_key_here
   PLAYER_NAME=YourInGameName
   ```

## 🏗️ Architecture: DX + AX

We follow **DX (Developer Experience)** and **AX (Agent Experience)** as first-class architecture standards.

### DX — Developer Experience
- **Unified entrypoint**: `./dev.sh` brings up the frontend, API, and replay watcher.
- **Predictable API**: REST under `/api` with a single discovery manifest.
- **Structured Relational RAG**: SQLite for deterministic retrieval instead of vector databases.
- **Self-Healing**: Automated data integrity monitoring and repair (Nexus Healer).

### AX — Agent Experience
- **Dual-interface**: Visual layer (React) for humans; structured data layer (JSON API + tools) for agents.
- **llms.txt**: LLM-oriented site guide at `/llms.txt`.
- **API discovery**: `GET /api/discovery` returns machine-readable endpoint descriptions.
- **WebMCP tools**: The app registers callable tools (e.g. `nexus_match_history`, `nexus_ask`, `nexus_map_stats`) via the Web Model Context API.

---

*Nexus Command Lab: Evolve your game.*
