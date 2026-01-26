# 🧠 Cerebrate: HOTS War Room

> "The difference between victory and defeat is often a single correct decision in the draft."

Cerebrate is an advanced tactical AI assistant designed for Heroes of the Storm players who want to bridge the gap between mechanical skill and strategic mastery. It transforms raw match history into actionable psychological and tactical advantages.

## 🚀 Key Features

### ⚔️ The War Room
Real-time drafting intelligence. Upload a screenshot of your loading screen or draft lobby, and Cerebrate will:
- **Identify Combatants**: Scans teammates and enemies for known historical data.
- **Predict Outcomes**: Calculates win probabilities based on map-specific mastery and team compositions.
- **Social Intelligence**: Flags "Synergy Anchors" (reliable allies) and "Apex Threats" (recurring nemesis rivals).

### 🎒 The Arsenal
A categorized view of your hero pool, preventing "experimental picks" on maps where you should be playing your best:
- **Proven**: High games, high win rate. Your reliable anchors.
- **Hot Streaks**: Momentum-based picks from the current season.
- **Pockets**: Low sample size but high performance "secret weapons."
- **Untapped**: Heroes you play well generally but have yet to master on specific maps.
- **Avoid**: Statistically confirmed weaknesses.

### 🧭 Map Directives
For every map in the rotation, Cerebrate defines a specific **Win Condition** (e.g., RACE, ZONE, PUSH) and recommends heroes that excel at executing that specific strategy.

### 📊 Data Provenance
Multi-source verification ensures your stats are accurate:
- **Blizzard Source**: Official totals and rank verification via screenshot ingestion.
- **Replay Parser**: Granular talent-level data and teammate/enemy interaction history.
- **Audit Logs**: Transparent history of how stats were calculated.

## 🧠 The Cerebrate Brain
The project's reasoning is driven by a collection of structured markdown protocols found in `.agent/brain/`. These protocols guide the AI's persona and logic:
- `MAP_RECOMMENDATIONS.md`: Logic for map-specific mastery.
- `SOCIAL_INTELLIGENCE_PROTOCOL.md`: How to classify rivals and allies.
- `BAN_RECOMMENDATIONS.md`: Protected asset logic for draft bans.
- `RANK_PROGRESSION.md`: Long-term tracking of your climb.

## 🛠️ Technology Stack
- **Frontend**: React, Vite, Tailwind CSS, Lucide Icons.
- **Backend**: Python (Flask), SQLite for persistent storage.
- **AI**: Next-generation **Google Gemini 3** (Vision + Pro/Flash) for clinical multimodal analysis.
- **Processing**: Custom Replay Parser for high-density JSON match forensics.

## ⚡ Gemini 3 Integration
Cerebrate is built to exploit the advanced capabilities of the Gemini 3 ecosystem:
- **Multimodal Loading Screen Analysis**: Uses Gemini 3 Vision to identify allies and enemies from raw game screenshots, mapping them to historical combat logs in milliseconds.
- **Relational RAG (Retrieval-Augmented Generation)**: Ingests massive JSON telemetry streams into Gemini 3's 1.0M+ token window, allowing for forensic-level analysis of positional data and tactical intent without semantic loss.
- **Autonomous Swarm Intelligence**: A multi-agent system (Scout, Analyst, Tactician) that utilizes Gemini 3's high-speed reasoning to provide live draft recommendations and post-game autopsies.
- **Zero-Failure Model Tiering**: Automated self-healing logic that rotates between Gemini 3 Pro, Flash, and Flash-Lite based on latency and quota state.

## 🚦 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Heroes of the Storm (running in Windowed or Windowed-Fullscreen for screenshots)

### Installation
1. Clone the repository.
2. Install frontend dependencies: `npm install`
3. Install backend dependencies: `pip install -r requirements.txt`
4. Set up your `.env` file with your Gemini API key:
   ```env
   GOOGLE_API_KEY=your_key_here
   PLAYER_NAME=YourInGameName
   ```

### Running the Application
1. Start the backend server: `./start_server.sh`
2. Start the frontend development server: `npm run dev`
3. Open `http://localhost:5173` in your browser.

## 📜 Strategic Directives
- **Data is Truth**: Always prioritize verified stats over generic meta advice.
- **Protect the Asset**: Identify your strongest hero for the map and build/ban around them.
- **Zero-Death Discipline**: High win rates on major maps come from positional excellence.

---
*Cerebrate: Evolve your game.*
