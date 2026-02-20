from flask import Blueprint, request, jsonify
import json
import time
import base64
from api.services.database import DatabaseManager
from api.services.intelligence_service import IntelligenceService
import os

verification_bp = Blueprint('verification', __name__, url_prefix='/api')
db = DatabaseManager()

def get_intelligence():
    api_key = os.environ.get('GEMINI_API_KEY')
    return IntelligenceService(db, api_key)

@verification_bp.route('/extract_stats_from_screenshot', methods=['POST'])
def extract_stats():
    """Extracts HotsLogs or Profile stats from a screenshot using Gemini Vision."""
    data = request.json or {}
    image_data = data.get('image') # Base64 encoded image
    
    if not image_data:
        return jsonify({"success": False, "error": "No image data provided"}), 400
        
    intel = get_intelligence()
    
    prompt = """
    Extract Heroes of the Storm stats from this screenshot.

    DETECT SCREEN TYPE:
    - If you see "Storm League" or "Ranked" with a season (e.g. "2026 Season 1"): set stat_type="season", screen_type="ranked"
    - If you see profile/collection/lifetime stats: set stat_type="lifetime", screen_type="profile_page"
    - If you see a single hero's stats: set stat_type="season", screen_type="heroes_profile", is_hero_view=true, viewed_hero="HeroName"

    DETECT SEASON (for ranked screens): Look for "Storm League, 20XX Season N" and set season_name (e.g. "2026 Season 1").

    EXTRACT: total_games (or games_played), wins, losses, win_rate, rank (e.g. "Bronze 3"), player_level.
    For maps: [{map: "MapName", wins: n, losses: n, win_rate: n}]
    For heroes: [{hero: "HeroName", games: n, wins: n, wr: n}]

    Return ONLY valid JSON, no markdown:
    {
      "stat_type": "season" | "lifetime",
      "screen_type": "ranked" | "profile_page" | "heroes_profile",
      "season_name": "2026 Season 1" | null,
      "is_hero_view": boolean,
      "viewed_hero": "HeroName" | null,
      "total_games": number,
      "wins": number,
      "losses": number,
      "win_rate": number,
      "rank": "string" | null,
      "player_level": number | null,
      "heroes": [{"hero": string, "games": number, "wins": number, "wr": number}],
      "maps": [{"map": string, "wins": number, "losses": number, "win_rate": number}]
    }
    Use games_played/totalGames if total_games not visible. Use 0 for missing numbers.
    """
    
    try:
        # Assuming IntelligenceService.model exists and can handle vision
        # This is a bit speculative on the internal structure of intel_service 
        # but matches the 'ask_agent' pattern.
        gen = intel.model
        if not gen:
            return jsonify({"success": False, "error": "AI not initialized. Set GEMINI_API_KEY."}), 500
        resp = gen.generate_content([prompt, {"mime_type": "image/png", "data": image_data.split(',')[-1]}])
        response_text = (resp.text or "").strip()
        if not response_text:
            return jsonify({"success": False, "error": "AI returned empty response. Try a different screenshot."}), 500

        # Parse JSON from response
        # Clean up any markdown blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        stats = json.loads(response_text)
        # Normalize keys for frontend compatibility
        if "games_played" in stats and "total_games" not in stats:
            stats["total_games"] = stats["games_played"]
        for h in stats.get("heroes", []) or []:
            if "name" in h and "hero" not in h:
                h["hero"] = h.pop("name", None)
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@verification_bp.route('/verify_stats', methods=['POST'])
def verify_stats():
    """Verify stats: compare extracted vs local, and optionally persist stats/hero_stats to player_profile."""
    data = request.json or {}
    extracted = data.get('extracted', {})
    stat_type = data.get('stat_type')
    stats = data.get('stats')
    hero_stats = data.get('hero_stats')
    season_slug = data.get('season_slug')

    if stats is not None and hero_stats is not None and stat_type in ('lifetime', 'season'):
        try:
            profile = db.get_kv('player_profile') or {}
            if not isinstance(profile, dict):
                profile = {}
            sl = profile.setdefault('rank_data', {}).setdefault('storm_league', {})
            hs = profile.setdefault('hero_stats', {})

            if stat_type == 'lifetime':
                sl['verified_lifetime'] = {
                    'total_games': stats.get('total_games'),
                    'wins': stats.get('wins'),
                    'losses': stats.get('losses'),
                    'win_rate': stats.get('win_rate'),
                }
                for h in hero_stats:
                    name = (h.get('hero') or '').strip()
                    if not name:
                        continue
                    if name not in hs:
                        hs[name] = {}
                    hs[name]['verified_lifetime'] = {
                        'games': h.get('games'),
                        'wr': h.get('wr'),
                        'level': h.get('level'),
                    }
            else:
                key = f'verified_{season_slug}' if season_slug else 'verified_season_2025_3'
                sl[key] = {
                    'total_games': stats.get('total_games'),
                    'wins': stats.get('wins'),
                    'losses': stats.get('losses'),
                    'win_rate': stats.get('win_rate'),
                }
                for h in hero_stats:
                    name = (h.get('hero') or '').strip()
                    if not name:
                        continue
                    if name not in hs:
                        hs[name] = {}
                    hs[name][key] = {
                        'games': h.get('games'),
                        'wr': h.get('wr'),
                        'level': h.get('level'),
                    }
            if data.get('season_name') and season_slug:
                profile['active_season'] = {
                    'slug': season_slug,
                    'name': data.get('season_name'),
                    'start_date': data.get('season_start_date') or '',
                }
            db.set_kv('player_profile', profile)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    if not extracted:
        return jsonify({"success": True, "message": "Stats saved."})

    try:
        with db._get_connection() as conn:
            try:
                cursor = conn.execute("SELECT key, value FROM global_account_stats")
                rows = cursor.fetchall()
                local_map = {row[0]: row[1] for row in rows}
            except Exception:
                local_map = {}
            local_games = int(local_map.get('lifetime_games_played', 0))
            ext_games = int(extracted.get('games_played', 0))
            diff_games = ext_games - local_games
            verification = {
                "games": {
                    "source": ext_games,
                    "local": local_games,
                    "delta": diff_games,
                    "status": "synchronized" if diff_games == 0 else "behind" if diff_games > 0 else "ahead"
                },
                "confidence": 0.85 if diff_games < 10 else 0.5,
                "needs_sync": diff_games > 0,
                "message": f"Source shows {diff_games} more games than local database." if diff_games > 0 else "Local data matches source telemetry."
            }
            return jsonify({"success": True, "verification": verification})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
