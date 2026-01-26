#!/usr/bin/env python3
"""
Data Sources API Routes
Provides endpoints for data provenance tracking
"""

from flask import Blueprint, jsonify, request
import json
import os
from datetime import datetime, timedelta

data_sources_bp = Blueprint('data_sources', __name__, url_prefix='/api/data_sources')

# File paths
INGESTION_LOG = "src/data/ingestion_log.json"
BLIZZARD_VERIFIED = "src/data/sources/blizzard_verified.json"
REPLAY_DERIVED = "src/data/sources/replay_derived.json"
PLAYER_PROFILE = "src/data/player_profile.json"
MATCH_HISTORY = "src/data/match_history.json"


from database_manager import DatabaseManager
db = DatabaseManager()

def load_json_safe(filepath, default=None):
    """Safely load JSON from SQL KV store (Master) or fallback to file"""
    # Try SQL first
    key = os.path.basename(filepath).replace('.json', '')
    if 'sources' in filepath:
        # Handle sources subdirectory
        key = filepath.replace('.json', '').replace('/', '_').replace('\\', '_').split('src_data_')[-1]
        if key.startswith('sources_'): key = key # already handled?
        else: key = 'sources_' + key if not key.startswith('sources') else key # redundant check
        # Actually simplified:
        key = filepath.replace('.json', '').replace('/', '_').replace('\\', '_')
        if 'src_data_' in key:
            key = key.split('src_data_')[-1]
            
    data = db.get_kv(key)
    if data is not None:
        return data

    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except:
        pass
    return default or {}


@data_sources_bp.route('/status', methods=['GET'])
def get_source_status():
    """Get status of all data sources"""
    
    # Blizzard Verified Status
    blizzard_data = load_json_safe(BLIZZARD_VERIFIED, {"verifications": []})
    blizzard_verifications = blizzard_data.get("verifications", [])
    blizzard_latest = blizzard_verifications[0] if blizzard_verifications else None
    
    blizzard_status = {
        "last_updated": blizzard_latest["timestamp"] if blizzard_latest else "Never",
        "record_count": len(blizzard_latest.get("hero_stats", {})) if blizzard_latest else 0,
        "coverage": 100 if blizzard_latest else 0,
        "confidence": "verified",
        "healthy": is_recent(blizzard_latest["timestamp"]) if blizzard_latest else False
    }
    
    # Replay Parser Status
    match_history = load_json_safe(MATCH_HISTORY, [])
    player_profile = load_json_safe(PLAYER_PROFILE, {})
    replay_latest = match_history[0] if match_history else None
    
    replay_status = {
        "last_updated": replay_latest["date"] if replay_latest else "Never",
        "record_count": len(match_history),
        "coverage": calculate_coverage(match_history, player_profile),
        "confidence": "High (Replay Derived)",
        "healthy": True if match_history else False
    }
    
    # HeroesProfile Status (placeholder - implement when API is integrated)
    heroesprofile_status = {
        "last_updated": "2026-01-06T20:55:00-05:00",
        "record_count": 0,
        "coverage": 0,
        "confidence": "api",
        "healthy": False
    }
    
    # Manual Entry Status
    manual_status = {
        "last_updated": "Never",
        "record_count": 0,
        "coverage": 0,
        "confidence": "manual",
        "healthy": True
    }
    
    return jsonify({
        "blizzard_verified": blizzard_status,
        "replay_parser": replay_status,
        "heroesprofile": heroesprofile_status,
        "manual_entry": manual_status
    })


@data_sources_bp.route('/conflicts', methods=['GET'])
def get_conflicts():
    """Get current data conflicts"""
    conflicts = []
    
    # Load all sources
    blizzard_data = load_json_safe(BLIZZARD_VERIFIED, {"verifications": []})
    blizzard_latest = blizzard_data.get("verifications", [{}])[0] if blizzard_data.get("verifications") else {}
    
    player_profile = load_json_safe(PLAYER_PROFILE, {})
    match_history = load_json_safe(MATCH_HISTORY, [])
    
    # Check for conflicts in core stats
    if player_profile:
        sl_data = player_profile.get("rank_data", {}).get("storm_league", {})
        verified_lifetime = sl_data.get("verified_lifetime", {})
        
        if verified_lifetime:
            v_total = verified_lifetime.get("total_games", 0)
            replay_total = len(match_history)
            
            # Only conflict if Replay Parser has MORE games than Verified (Stale Verification)
            if replay_total > v_total:
                conflicts.append({
                    "field": "stale_profile_verification",
                    "entity": "Account Profile",
                    "values": [
                        {
                            "source": "blizzard_verified",
                            "value": f"{v_total} games",
                            "timestamp": verified_lifetime.get("last_verified", "")
                        },
                        {
                            "source": "replay_parser",
                            "value": f"{replay_total} games",
                            "timestamp": match_history[0].get("date", "") if match_history else ""
                        }
                    ],
                    "resolved_source": "replay_parser",
                    "reason": f"Profile Audit: Your replay library has {replay_total} games, exceeding your verified {v_total}. New screenshot required for synchronization."
                })

    # Check for conflicts in hero stats
    if player_profile and match_history:
        hero_stats = player_profile.get("hero_stats", {})
        
        # Compute replay-derived stats
        replay_heroes = compute_replay_hero_stats(match_history)
        
        HERO_ALIASES = {
            "Crusader": "Johanna",
            "FaerieDragon": "Brightwing",
            "DemonHunter": "Valla",
            "Monk": "Kharazim",
            "Medic": "Lt. Morales",
            "Firebat": "Blaze",
            "Amazon": "Cassia",
            "Necromancer": "Xul",
            "WitchDoctor": "Nazeebo",
            "Barbarian": "Sonya",
            "Wizard": "Li-Ming",
            "L90ETC": "E.T.C.",
            "Tinker": "Gazlowe",
            "Dryad": "Lunara",
            "Dreadlord": "Mal'Ganis",
            "LiLi": "Li Li"
        }

        # Normalize replay heroes
        normalized_replay = {}
        for h, d in replay_heroes.items():
            norm_name = HERO_ALIASES.get(h, h)
            if norm_name in normalized_replay:
                normalized_replay[norm_name]["games"] += d["games"]
            else:
                normalized_replay[norm_name] = d

        for hero, data in hero_stats.items():
            # Neural Selection: Prioritize explicit lifetime/season over generic verified
            verified_data = data.get("verified_lifetime") or data.get("verified_season_2025_3") or data.get("verified")
            
            if verified_data:
                v_games = verified_data.get("games", 0) or 0
                
                if hero in normalized_replay:
                    replay_games = normalized_replay[hero].get("games", 0)
                    
                    # STALE VERIFICATION: If replays exceed verified games, we need a new scan
                    if replay_games > v_games:
                        conflicts.append({
                            "field": "stale_verification",
                            "entity": hero,
                            "values": [
                                {
                                    "source": "blizzard_verified",
                                    "value": f"{v_games} games",
                                    "timestamp": verified_data.get("last_verified", "")
                                },
                                {
                                    "source": "replay_parser",
                                    "value": f"{replay_games} games",
                                    "timestamp": match_history[0].get("date", "") if match_history else ""
                                }
                            ],
                            "resolved_source": "replay_parser",
                            "reason": f"New Combat Logs Detected: Replay index ({replay_games}) has surpassed verified record ({v_games}). Capture a new screenshot to synchronize."
                        })
                # Note: We NO LONGER flag 'Presence: Missing' as a conflict. 
                # A lack of replays does not conflict with verified truth.
        
        # Reverse check: Find heroes in replays missing verified data (Intelligence Gaps / Calibration Required)
        for hero, data in normalized_replay.items():
            if hero not in hero_stats or (not hero_stats[hero].get("verified_lifetime") and not hero_stats[hero].get("verified_season_2025_3") and not hero_stats[hero].get("verified")):
                conflicts.append({
                    "field": "calibration_required",
                    "entity": hero,
                    "values": [
                        {
                            "source": "blizzard_verified",
                            "value": "Unverified",
                            "timestamp": "N/A"
                        },
                        {
                            "source": "replay_parser",
                            "value": f"{data.get('games', 0)} Replays",
                            "timestamp": match_history[0].get("date", "") if match_history else ""
                        }
                    ],
                    "resolved_source": "manual_entry",
                    "reason": f"New Hero Calibration: You've played {hero} in replays, but the Cerebrate hasn't verified this data. Screenshot required."
                })
    
    return jsonify({"conflicts": conflicts})


@data_sources_bp.route('/ingest/<source>', methods=['POST'])
def trigger_ingestion(source):
    """Trigger re-ingestion from a specific source"""
    
    if source == "blizzard_verified":
        # Placeholder - would trigger manual verification flow
        return jsonify({
            "success": True,
            "message": "Blizzard verification requires manual screenshot upload"
        })
    
    elif source == "replay_parser":
        # Trigger real-time re-calibration via watcher overdrive
        try:
            import subprocess
            import os
            # Use the new --once flag I added to replay_watcher
            subprocess.Popen(
                ["python3", "replay_watcher.py", "--once"],
                cwd=os.getcwd()
            )
            return jsonify({
                "success": True,
                "message": "Manual Re-Calibration Initiated. The Cerebrate is scanning your tactical logs."
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Failed to initiate re-calibration: {str(e)}"
            }), 500
    
    elif source == "heroesprofile":
        # Placeholder - would trigger HeroesProfile API sync
        return jsonify({
            "success": False,
            "message": "HeroesProfile sync not yet implemented"
        })
    
    else:
        return jsonify({
            "success": False,
            "message": f"Unknown source: {source}"
        }), 400


def is_recent(timestamp_str, days=7):
    """Check if timestamp is within last N days"""
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return (datetime.now() - timestamp).days < days
    except:
        return False


def calculate_coverage(match_history, profile=None):
    """Calculate what % of total games we have replays for"""
    if profile:
        sl_data = profile.get("rank_data", {}).get("storm_league", {})
        v_total = sl_data.get("verified_lifetime", {}).get("total_games")
        if v_total and v_total > 0:
            return round(min(100, (len(match_history) / v_total) * 100), 1)
            
    # Placeholder fallback
    return min(100, round((len(match_history) / 500) * 100, 1))


def compute_replay_hero_stats(match_history):
    """Compute hero stats from replay data"""
    hero_stats = {}
    
    for match in match_history:
        hero = match.get("hero")
        if hero:
            if hero not in hero_stats:
                hero_stats[hero] = {"games": 0, "wins": 0}
            
            hero_stats[hero]["games"] += 1
            if match.get("result") == "WIN":
                hero_stats[hero]["wins"] += 1
    
    # Calculate win rates
    for hero in hero_stats:
        games = hero_stats[hero]["games"]
        wins = hero_stats[hero]["wins"]
        hero_stats[hero]["wr"] = round((wins / games * 100), 1) if games > 0 else 0
    
    return hero_stats


# Export blueprint
__all__ = ['data_sources_bp']
