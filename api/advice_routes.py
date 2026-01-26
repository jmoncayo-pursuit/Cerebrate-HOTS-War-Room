"""
Learning Coach API - Advice Logging & Feedback System

Endpoints:
- POST /api/save_advice - Save AI advice for tracking
- POST /api/link_replay_to_advice - Link replay outcome to advice
- POST /api/submit_feedback - Submit user feedback on advice
- GET /api/advice_stats - Get advice effectiveness stats
"""

from flask import Blueprint, request, jsonify
import json
import os
from datetime import datetime
import uuid
from api.logger import ColoredLogger

advice_bp = Blueprint('advice', __name__, url_prefix='/api')

ADVICE_LOG_PATH = 'src/data/advice_log.json'


def load_advice_log():
    """Load advice log from file."""
    if not os.path.exists(ADVICE_LOG_PATH):
        return {
            "advice_history": [],
            "metadata": {
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_advice_given": 0,
                "total_advice_followed": 0,
                "total_advice_ignored": 0
            },
            "stats": {
                "overall_effectiveness": {
                    "followed_win_rate": 0,
                    "ignored_win_rate": 0,
                    "total_games_tracked": 0
                },
                "by_hero": {},
                "by_map": {}
            }
        }
    
    with open(ADVICE_LOG_PATH, 'r') as f:
        return json.load(f)


def save_advice_log(data):
    """Save advice log to file."""
    data['metadata']['last_updated'] = datetime.now().isoformat()
    
    os.makedirs(os.path.dirname(ADVICE_LOG_PATH), exist_ok=True)
    with open(ADVICE_LOG_PATH, 'w') as f:
        json.dump(data, f, indent=2)


@advice_bp.route('/save_advice', methods=['POST'])
def save_advice():
    """
    Save AI advice for future tracking.
    
    Request body:
    {
      "context": {
        "map": "Alterac Pass",
        "user_question": "What should I play?"
      },
      "advice_given": {
        "hero": "Gazlowe",
        "build": "Build B (Ark Reaktor)",
        "reasoning": "55.66% global WR, your comfort pick"
      }
    }
    
    Returns:
    {
      "advice_id": "adv_abc123",
      "saved": true
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        log = load_advice_log()
        
        # Generate unique ID
        advice_id = f"adv_{uuid.uuid4().hex[:8]}"
        
        # Create advice entry
        advice_entry = {
            "id": advice_id,
            "timestamp": datetime.now().isoformat(),
            "context": data.get('context', {}),
            "advice_given": data.get('advice_given', {}),
            "action_taken": None,  # Will be filled when replay is linked
            "feedback": None  # Will be filled when user submits feedback
        }
        
        # Add to history
        log['advice_history'].append(advice_entry)
        log['metadata']['total_advice_given'] += 1
        
        save_advice_log(log)
        
        return jsonify({
            "advice_id": advice_id,
            "saved": true,
            "message": "Advice saved for post-game review"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@advice_bp.route('/link_replay_to_advice', methods=['POST'])
def link_replay_to_advice():
    """
    Link a replay outcome to previously given advice.
    
    Request body:
    {
      "advice_id": "adv_abc123",
      "followed": true,
      "replay_id": "replay_xyz",
      "result": "WIN",
      "hero_played": "Gazlowe",
      "map": "Alterac Pass"
    }
    
    Returns:
    {
      "linked": true,
      "advice_effectiveness": "67% (2W-1L)"
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        log = load_advice_log()
        
        # Find advice entry
        advice_entry = next(
            (a for a in log['advice_history'] if a['id'] == data['advice_id']),
            None
        )
        
        if not advice_entry:
            return jsonify({"error": "Advice ID not found"}), 404
        
        # Update action taken
        advice_entry['action_taken'] = {
            "followed": data.get('followed', False),
            "replay_id": data.get('replay_id'),
            "result": data.get('result'),
            "hero_played": data.get('hero_played'),
            "map": data.get('map'),
            "timestamp": datetime.now().isoformat()
        }
        
        # Update metadata
        if data.get('followed'):
            log['metadata']['total_advice_followed'] += 1
        else:
            log['metadata']['total_advice_ignored'] += 1
        
        # Update stats
        update_stats(log, advice_entry, data)
        
        save_advice_log(log)
        
        # Calculate effectiveness for this hero/map combo
        effectiveness = calculate_effectiveness(log, data.get('hero_played'), data.get('map'))
        
        return jsonify({
            "linked": True,
            "advice_effectiveness": effectiveness,
            "message": "Replay linked to advice"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@advice_bp.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """
    Submit user feedback on advice.
    
    Request body:
    {
      "advice_id": "adv_abc123",
      "rating": 5,
      "comment": "Worked great, dominated lane"
    }
    
    Returns:
    {
      "feedback_saved": true
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        log = load_advice_log()
        
        # Find advice entry
        advice_entry = next(
            (a for a in log['advice_history'] if a['id'] == data['advice_id']),
            None
        )
        
        if not advice_entry:
            return jsonify({"error": "Advice ID not found"}), 404
        
        # Update feedback
        advice_entry['feedback'] = {
            "user_rating": data.get('rating'),
            "user_comment": data.get('comment'),
            "timestamp": datetime.now().isoformat()
        }
        
        save_advice_log(log)
        
        return jsonify({
            "feedback_saved": True,
            "message": "Thank you for your feedback!"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@advice_bp.route('/advice_stats', methods=['GET'])
def get_advice_stats():
    """
    Get advice effectiveness statistics.
    
    Query params:
    - hero: Filter by hero (optional)
    - map: Filter by map (optional)
    
    Returns:
    {
      "overall": {
        "followed_win_rate": 67,
        "ignored_win_rate": 45,
        "total_games": 15
      },
      "by_hero": {...},
      "by_map": {...},
      "recent_advice": [...]
    }
    """
    try:
        log = load_advice_log()
        hero_filter = request.args.get('hero')
        map_filter = request.args.get('map')
        
        # Filter advice history
        filtered_advice = log['advice_history']
        
        if hero_filter:
            filtered_advice = [
                a for a in filtered_advice
                if a.get('advice_given', {}).get('hero') == hero_filter
            ]
        
        if map_filter:
            filtered_advice = [
                a for a in filtered_advice
                if a.get('context', {}).get('map') == map_filter
            ]
        
        # Calculate stats
        stats = calculate_filtered_stats(filtered_advice)
        
        return jsonify({
            "overall": stats,
            "by_hero": log['stats'].get('by_hero', {}),
            "by_map": log['stats'].get('by_map', {}),
            "recent_advice": filtered_advice[-10:]  # Last 10
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def update_stats(log, advice_entry, data):
    """Update statistics after linking replay."""
    hero = data.get('hero_played')
    map_name = data.get('map')
    result = data.get('result')
    followed = data.get('followed')
    
    # Update overall stats
    log['stats']['overall_effectiveness']['total_games_tracked'] += 1
    
    # Update by hero
    if hero not in log['stats']['by_hero']:
        log['stats']['by_hero'][hero] = {
            "followed_wins": 0,
            "followed_losses": 0,
            "ignored_wins": 0,
            "ignored_losses": 0
        }
    
    if followed:
        if result == 'WIN':
            log['stats']['by_hero'][hero]['followed_wins'] += 1
        else:
            log['stats']['by_hero'][hero]['followed_losses'] += 1
    else:
        if result == 'WIN':
            log['stats']['by_hero'][hero]['ignored_wins'] += 1
        else:
            log['stats']['by_hero'][hero]['ignored_losses'] += 1
    
    # Update by map
    if map_name not in log['stats']['by_map']:
        log['stats']['by_map'][map_name] = {
            "followed_wins": 0,
            "followed_losses": 0,
            "ignored_wins": 0,
            "ignored_losses": 0
        }
    
    if followed:
        if result == 'WIN':
            log['stats']['by_map'][map_name]['followed_wins'] += 1
        else:
            log['stats']['by_map'][map_name]['followed_losses'] += 1
    else:
        if result == 'WIN':
            log['stats']['by_map'][map_name]['ignored_wins'] += 1
        else:
            log['stats']['by_map'][map_name]['ignored_losses'] += 1
    
    # Recalculate overall win rates
    recalculate_overall_stats(log)


def recalculate_overall_stats(log):
    """Recalculate overall win rates."""
    followed_wins = 0
    followed_total = 0
    ignored_wins = 0
    ignored_total = 0
    
    for advice in log['advice_history']:
        action = advice.get('action_taken')
        if not action:
            continue
        
        if action.get('followed'):
            followed_total += 1
            if action.get('result') == 'WIN':
                followed_wins += 1
        else:
            ignored_total += 1
            if action.get('result') == 'WIN':
                ignored_wins += 1
    
    log['stats']['overall_effectiveness']['followed_win_rate'] = (
        round((followed_wins / followed_total) * 100, 1) if followed_total > 0 else 0
    )
    log['stats']['overall_effectiveness']['ignored_win_rate'] = (
        round((ignored_wins / ignored_total) * 100, 1) if ignored_total > 0 else 0
    )


def calculate_effectiveness(log, hero, map_name):
    """Calculate effectiveness string for specific hero/map."""
    relevant_advice = [
        a for a in log['advice_history']
        if a.get('advice_given', {}).get('hero') == hero
        and a.get('context', {}).get('map') == map_name
        and a.get('action_taken') is not None
        and a.get('action_taken', {}).get('followed') == True
    ]
    
    if not relevant_advice:
        return "No data yet"
    
    wins = sum(1 for a in relevant_advice if a['action_taken']['result'] == 'WIN')
    total = len(relevant_advice)
    losses = total - wins
    win_rate = round((wins / total) * 100) if total > 0 else 0
    
    return f"{win_rate}% ({wins}W-{losses}L)"


def calculate_filtered_stats(advice_list):
    """Calculate stats for filtered advice list."""
    followed_wins = 0
    followed_total = 0
    ignored_wins = 0
    ignored_total = 0
    
    for advice in advice_list:
        action = advice.get('action_taken')
        if not action:
            continue
        
        if action.get('followed'):
            followed_total += 1
            if action.get('result') == 'WIN':
                followed_wins += 1
        else:
            ignored_total += 1
            if action.get('result') == 'WIN':
                ignored_wins += 1
    
    return {
        "followed_win_rate": round((followed_wins / followed_total) * 100, 1) if followed_total > 0 else 0,
        "ignored_win_rate": round((ignored_wins / ignored_total) * 100, 1) if ignored_total > 0 else 0,
        "total_games": followed_total + ignored_total,
        "followed_games": followed_total,
        "ignored_games": ignored_total
    }
