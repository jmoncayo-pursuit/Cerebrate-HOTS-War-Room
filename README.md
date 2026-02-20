
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
- **FORENSIC ANALYST**: Post-game forensic analysis, identifying subtle mechanical failures and critical turning points. 
- **SCOUT**: Draft intelligence, hero recommendations, ban priorities
- **TACTICIAN**: Map-specific strategies, rotation timing, objective prioritization
- **SOCIAL**: Player synergy analysis, nemesis tracking, duo queue recommendations
- **AUDIT**: Quality assurance agent that verifies AI hallucinations against replay truth.
- **MECHANICAL**: Specialized micro-analysis for specific heroes (Stitches Hooks, Kharazim Dashes, Azmodan Stacks).

### 📊 Data Provenance
Multi-source verification ensures your stats are accurate:
- **Blizzard Source**: Official totals and rank verification via screenshot ingestion
- **Forensic Replay Parser**: Granular talent-level data, DC detection, and teammate/enemy interaction history (v3.2)
   - *New*: Tracks Game Modes (Storm League vs QM) and Disconnects.
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
- **AI**: Multi-model orchestration (Gemini 2.0, GPT-4o, Claude 3.5) for optimized domain performance
- **Processing**: Custom Python Replay Parser (MPQ based) for high-density JSON match forensics
- **Architecture**: Swarm of specialized agents (Auditor, Analyst, Social) routed to the best-fit model for the task

## 🧠 Cognitive Architecture
Cerebrate leverages a best-in-class multi-model strategy, routing tasks to the most effective intelligence available:
- **Multimodal Vision**: Uses Vision AI to identify allies and enemies from screenshots
- **Structured Relational RAG**: Ingests massive JSON telemetry streams into large token windows for forensic-level analysis
- **Autonomous Swarm Intelligence**: Multi-agent system (Scout, Analyst, Tactician, etc.) for specialized recommendations
- **Truth Validation**: Dedicated "Auditor" agent that cross-references AI narrative against hard replay data to prevent hallucinations.

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

2. Run the unifying dev script (Handles backend, frontend, and environment):
   ```bash
   chmod +x dev.sh
   ./dev.sh
   ```

3. Set up your `.env` file with your Gemini API key (created automatically if missing):
   ```env
   GOOGLE_API_KEY=your_key_here
   PLAYER_NAME=YourInGameName
   ```

### Running the Application
The `./dev.sh` script manages all services:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Replay Watcher**: Auto-ingests new replays from your folder.

### Agent experience (AX) / WebMCP
The app exposes tools to in-browser AI agents via the [Web Model Context API](https://github.com/webmachinelearning/webmcp) (polyfill: `@mcp-b/global`). When the War Room is open, agents can call e.g. `cerebrate_match_history`, `cerebrate_ask`, `cerebrate_map_stats` without scraping the UI. To test: enable **"WebMCP for testing"** in `chrome://flags`, or install the [MCP-B Extension](https://chromewebstore.google.com/detail/mcp-b-extension/daohopfhkdelnpemnhlekblhnikhdhfa). See `/llms.txt` for API overview and `/api/discovery` for endpoint list.

### Cursor MCP (development)
The same Cerebrate API is exposed to **Cursor** via a project MCP server so the IDE can call War Room tools during development (one API: UI, WebMCP, and Cursor). Project config: **`.cursor/mcp.json`** — starts `scripts/cerebrate_mcp_server.py` (stdio). Ensure the Cerebrate API is running (`http://localhost:8000`) when using Cursor tools. On Windows, set `"command"` in `mcp.json` to your venv Python path (e.g. `".\\venv\\Scripts\\python.exe"`).

## 📜 Strategic Directives
- **Data is Truth**: Always prioritize verified stats over generic meta advice
- **Protect the Asset**: Identify your strongest hero for the map and build/ban around them
- **Zero-Death Discipline**: High win rates on major maps come from positional excellence

## 🚧 In Development
Features currently being developed:
- **Universal Mastery Dashboard**: A unified view of all hero progression.
- **Real-Time Draft Assistant Overlay**: (Planned) In-game overlay for draft phase.

## 🏗️ Architecture: DX + AX

We follow **DX (Developer Experience)** and **AX (Agent Experience)** as first-class architecture standards.

### DX — Developer Experience
- **Unified dev entrypoint**: `./dev.sh` brings up frontend, API, replay watcher, and optional Chrome Canary neural link.
- **Predictable API**: REST under `/api` with a single discovery manifest; see `/api/discovery`.
- **Structured Relational RAG**: SQLite for deterministic retrieval instead of vector databases.
- **Lean Context**: Agents receive only essential data (top 10 heroes, last 5 matches) to preserve token budget.
- **Temporal Awareness**: AI adjusts recommendations based on time-of-day performance patterns.
- **Self-Healing**: Automated data integrity monitoring and repair (Quartermaster/Healer).

### AX — Agent Experience
- **Dual-interface**: Visual layer (React) for humans; structured data layer (JSON API + tools) for agents. Agents use the API; they do not scrape the UI.
- **llms.txt**: LLM-oriented site guide at `/llms.txt` (project summary, API file list, optional links). Follows [llms.txt](https://llmstxt.org/); tells agents what the site is and which endpoints to use.
- **API discovery**: `GET /api/discovery` returns `{ llms_txt, endpoints: [{ method, path, description }] }` for machine-readable discovery.
- **WebMCP tools**: When the War Room is loaded, the app registers callable tools (e.g. `cerebrate_match_history`, `cerebrate_ask`, `cerebrate_map_stats`, `cerebrate_hero_dossier`) via the [Web Model Context API](https://github.com/webmachinelearning/webmcp) (polyfill: `@mcp-b/global`). In-browser agents invoke these instead of DOM actuation.
- **Semantic + JSON-LD**: `index.html` uses Schema.org `WebApplication` JSON-LD, `<main role="main">`, a visually-hidden `<header>` with site title/description for crawlers, meta description, and `<link rel="alternate" href="/llms.txt">` for agent and crawler discovery.
- **Sitemap**: `public/sitemap.xml` lists `/` and `/llms.txt` for discoverability (see [agent-friendly websites](https://prerender.io/blog/how-to-build-ai-agent-friendly-websites/)).
- **Prerendering for AI crawlers**: Crawler User-Agents (GPTBot, Claude, Perplexity, etc.) receive pre-rendered HTML so the React app is visible to AI search. Production: `npm run build && npm run serve` (Express + Puppeteer). Dev: set `PRERENDER_DEV=1` when running `npm run dev` to enable.

The War Room is both an **AI copilot** (draft intel, replay forensics, map mastery) and an **agent-ready surface** (llms.txt, discovery, WebMCP tools), so external agents can use and improve alongside the system.

---

*Cerebrate: Evolve your game.*
