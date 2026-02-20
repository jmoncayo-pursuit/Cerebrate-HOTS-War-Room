#!/usr/bin/env python3
"""
MCP server that exposes Cerebrate War Room API as tools for Cursor (and other MCP clients).
Same tool set as WebMCP in the frontend: one API, consumed by UI, browser agents, and IDE.
Run with: CEREBRATE_API_URL=http://localhost:8000 python scripts/cerebrate_mcp_server.py
Configure in Cursor: .cursor/mcp.json
"""
import os
import sys
import json
import urllib.error
import urllib.parse
import urllib.request

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Install mcp: pip install mcp", file=sys.stderr)
    sys.exit(1)

BASE = os.environ.get("CEREBRATE_API_URL", "http://localhost:8000")

mcp = FastMCP(
    "Cerebrate War Room",
    instructions="Cerebrate API tools: health, match history, player profile, map stats, hero dossier, ask, strategies. Same surface as llms.txt and WebMCP.",
)


def _api(path: str, method: str = "GET", body: str | None = None) -> dict | list:
    url = f"{BASE}/api{path}"
    req = urllib.request.Request(url, method=method, data=body.encode() if body else None)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "message": e.read().decode() if e.fp else str(e)}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def cerebrate_health() -> str:
    """Check Cerebrate API health and version."""
    data = _api("/health")
    return json.dumps(data, indent=2)


@mcp.tool()
def cerebrate_match_history(limit: int = 100, search: str = "") -> str:
    """Get the player's match history (replays). Optional limit and search query."""
    q = f"limit={limit}&pagination=true"
    if search:
        q += f"&search={urllib.parse.quote(search)}"
    data = _api(f"/match_history?{q}")
    if data.get("error"):
        return json.dumps(data)
    list_ = data.get("matches", data) if isinstance(data, dict) else data
    out = {"count": len(list_) if isinstance(list_, list) else 0, "matches": (list_ or [])[:20]}
    return json.dumps(out, indent=2)


@mcp.tool()
def cerebrate_player_profile() -> str:
    """Get the current player profile (toon, region, stats summary)."""
    data = _api("/player_profile")
    return json.dumps(data, indent=2)


@mcp.tool()
def cerebrate_map_stats() -> str:
    """Get map performance stats (games, wins, losses, win_rate per map)."""
    data = _api("/map_stats")
    return json.dumps(data if isinstance(data, list) else data, indent=2)


@mcp.tool()
def cerebrate_hero_dossier(hero: str) -> str:
    """Get tactical dossier for a hero (builds, strengths, map fit)."""
    if not hero:
        return json.dumps({"error": "hero is required"})
    data = _api(f"/hero_dossier?hero={urllib.parse.quote(hero)}")
    return json.dumps(data, indent=2)


@mcp.tool()
def cerebrate_ask(question: str) -> str:
    """Ask Cerebrate a natural-language question (draft, strategy, stats). Sends to the War Room AI."""
    if not question:
        return json.dumps({"error": "question is required"})
    data = _api("/chat", method="POST", body=json.dumps({"message": question}))
    if data.get("error"):
        return json.dumps(data)
    return data.get("response", json.dumps(data))


@mcp.tool()
def cerebrate_strategies() -> str:
    """Get current draft/strategy config (roster constraints, strategies)."""
    data = _api("/strategies")
    return json.dumps(data, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
