#!/usr/bin/env python3
"""
Nexus MCP Server
Exposes the Nexus Command Lab API as tools for Cursor, Windsurf, and other MCP clients.
Enables AI Agents to query match history, hero dossiers, and tactical intelligence directly.
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

# Configuration: Points to the Nexus API Server
BASE = os.environ.get("NEXUS_API_URL", "http://localhost:8000")

mcp = FastMCP(
    "Nexus Command Lab",
    instructions="Nexus Tactical Tools: Access player profiles, match history, map archives, and hero dossiers. Use these tools to provide data-driven HOTS advice.",
)

def _api(path: str, method: str = "GET", body: str | None = None) -> dict | list:
    """Internal helper to communicate with the Nexus API core."""
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
def nexus_health() -> str:
    """Check Nexus Command Lab API health and version."""
    data = _api("/health")
    return json.dumps(data, indent=2)

@mcp.tool()
def nexus_match_history(limit: int = 100, search: str = "") -> str:
    """
    Retrieve player match history.
    Args:
        limit: Max matches to fetch (default 100).
        search: Optional filter (map name or hero).
    """
    q = f"limit={limit}&pagination=true"
    if search:
        q += f"&search={urllib.parse.quote(search)}"
    data = _api(f"/match_history?{q}")
    if data.get("error"):
        return json.dumps(data)
    list_ = data.get("matches", data) if isinstance(data, dict) else data
    # Return count and a slice of the most recent for token efficiency
    out = {"count": len(list_) if isinstance(list_, list) else 0, "matches": (list_ or [])[:20]}
    return json.dumps(out, indent=2)

@mcp.tool()
def nexus_player_profile() -> str:
    """Get the current player profile (Toon, Region, Rank, and Stats summary)."""
    data = _api("/player_profile")
    return json.dumps(data, indent=2)

@mcp.tool()
def nexus_map_stats() -> str:
    """Get map performance analytics (Games played, Wins/Losses, and Win Rate per map)."""
    data = _api("/map_stats")
    return json.dumps(data, indent=2)

@mcp.tool()
def nexus_hero_dossier(hero: str) -> str:
    """
    Fetch a full tactical dossier for a specific hero.
    Includes builds, map synergies, nemesis analysis, and AI-generated forensic verdicts.
    """
    if not hero:
        return json.dumps({"error": "hero name is required"})
    data = _api(f"/hero_dossier?hero={urllib.parse.quote(hero)}")
    return json.dumps(data, indent=2)

@mcp.tool()
def nexus_intel_query(question: str) -> str:
    """
    Consult the Nexus Agentic Brain with a natural language query.
    Use for draft pick suggestions, counter-intel, or complex tactical questions.
    """
    if not question:
        return json.dumps({"error": "question is required"})
    data = _api("/nexus/ask", method="POST", body=json.dumps({"query": question}))
    if data.get("error"):
        return json.dumps(data)
    return data.get("response", json.dumps(data))

@mcp.tool()
def nexus_config_manifest() -> str:
    """Get the master Nexus configuration (roster constraints, active season, and strategy overrides)."""
    data = _api("/nexus_config")
    return json.dumps(data, indent=2)

if __name__ == "__main__":
    mcp.run(transport="stdio")
