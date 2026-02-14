# 🧠 Cerebrate: HOTS War Room

> "The difference between victory and defeat is often a single correct decision in the draft."

Cerebrate is an advanced tactical AI assistant designed for Heroes of the Storm players who want to bridge the gap between mechanical skill and strategic mastery. It transforms raw match history into actionable psychological and tactical advantages through multi-agent AI analysis and forensic match review.

## 🚀 Key Features

### ⚔️ The War Room
Real-time drafting intelligence. Upload a screenshot of your loading screen or draft lobby, and Cerebrate will:
- **Identify Combatants**: Scans teammates and enemies for known historical data
- **Predict Outcomes**: Calculates win probabilities based on map-specific mastery and team compositions
- **Social Intelligence**: Flags "Synergy Anchors" (reliable allies) and "Apex Threats" (recurring nemesis rivals)

### 🎒 The Arsenal
A categorized view of your hero pool, preventing "experimental picks" on maps where you should be playing your best:
- **Proven**: High games, high win rate. Your reliable anchors
- **Hot Streaks**: Momentum-based picks from the current season
- **Pockets**: Low sample size but high performance "secret weapons"
- **Untapped**: Heroes you play well generally but have yet to master on specific maps
- **Avoid**: Statistically confirmed weaknesses

### 🧭 Map Directives
For every map in the rotation, Cerebrate defines a specific **Win Condition** (e.g., RACE, ZONE, PUSH) and recommends heroes that excel at executing that specific strategy.

### 🤖 Multi-Agent AI System
Cerebrate uses a specialized swarm of AI agents, each optimized for specific domains:
- **ANALYST**: Post-game forensic analysis, critical mistakes, win conditions
- **SCOUT**: Draft intelligence, hero recommendations, ban priorities
- **TACTICIAN**: Map-specific strategies, rotation timing, objective prioritization
- **SOCIAL**: Player synergy analysis, nemesis tracking, duo queue recommendations
- **COACH**: Improvement roadmap generation, skill progression tracking
- **QUARTERMASTER**: Data integrity monitoring, ingestion health, system diagnostics

The **Cerebrate Orchestrator** intelligently routes queries to the appropriate specialist based on context and keywords.

### 📊 Data Provenance
Multi-source verification ensures your stats are accurate:
- **Blizzard Source**: Official totals and rank verification via screenshot ingestion
- **Replay Parser**: Granular talent-level data and teammate/enemy interaction history
- **Audit Logs**: Transparent history of how stats were calculated
- **Source Attribution**: Every stat displays its source (Verified/Parsed/Baseline)

## 🧠 The Cerebrate Brain
The project's reasoning is driven by structured markdown protocols in `.agent/brain/`:
- `MAP_RECOMMENDATIONS.md`: Logic for map-specific mastery
- `SOCIAL_INTELLIGENCE_PROTOCOL.md`: How to classify rivals and allies
- `BAN_RECOMMENDATIONS.md`: Protected asset logic for draft bans
- `RANK_PROGRESSION.md`: Long-term tracking of your climb

## 🛠️ Technology Stack
- **Frontend**: React, Vite, Tailwind CSS, Lucide Icons, Framer Motion
- **Backend**: Python (Flask), SQLite for persistent storage
- **AI**: Google Gemini for multimodal analysis
- **Processing**: Custom Replay Parser for high-density JSON match forensics
- **Architecture**: Multi-agent orchestrator with specialized AI agents

## ⚡ Gemini Integration
Cerebrate exploits advanced Gemini capabilities:
- **Multimodal Loading Screen Analysis**: Uses Gemini Vision to identify allies and enemies from screenshots
- **Structured Relational RAG**: Ingests massive JSON telemetry streams into Gemini's 1M+ token window for forensic-level analysis
- **Autonomous Swarm Intelligence**: Multi-agent system (Scout, Analyst, Tactician, etc.) for specialized recommendations
- **Quota Management**: Intelligent token budgeting and model tiering

## 🚦 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Gemini API key
- Heroes of the Storm (for replay file generation)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/jmoncayo-pursuit/Cerebrate-HOTS-War-Room.git
   cd Cerebrate-HOTS-War-Room
   ```

2. Install frontend dependencies:
   ```bash
   npm install
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your `.env` file with your Gemini API key:
   ```env
   GOOGLE_API_KEY=your_key_here
   PLAYER_NAME=YourInGameName
   ```

### Running the Application
1. Start the unified War Room environment:
   ```bash
   npm start
   ```
   This launches:
   - Frontend dev server (http://localhost:5173)
   - Flask API server (http://localhost:5001)
   - Replay watcher service (auto-processes new replays)

2. Open `http://localhost:5173` in your browser

## 📜 Strategic Directives
- **Data is Truth**: Always prioritize verified stats over generic meta advice
- **Protect the Asset**: Identify your strongest hero for the map and build/ban around them
- **Zero-Death Discipline**: High win rates on major maps come from positional excellence

## 🚧 In Development
Features currently being developed:
- **Hooks System**: Quality validation pipeline for AI-generated summaries (inspired by Gemini CLI)
  - Context injection for recent match history
  - Summary validation with auto-retry
  - Caching to prevent duplicate API calls
  - See `agents/hooks_manager.py` and test scripts in `scripts/`

## 🏗️ Architecture Highlights
- **Structured Relational RAG**: Uses SQLite for deterministic retrieval instead of vector databases
- **Lean Context**: Agents receive only essential data (top 10 heroes, last 5 matches) to preserve token budget
- **Temporal Awareness**: AI adjusts recommendations based on time of day performance patterns
- **Self-Healing**: Automated data integrity monitoring and repair via Quartermaster agent

---

*Cerebrate: Evolve your game.*
