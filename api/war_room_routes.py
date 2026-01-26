import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify

war_room_bp = Blueprint('war_room', __name__, url_prefix='/api')

CONFIG_FILE = os.path.join('src', 'data', 'cerebrate_config.json')
HERO_STATS_FILE = os.path.join('src', 'data', 'hero_stats.json')
LOGS_DIR = 'logs'

from database_manager import DatabaseManager
db = DatabaseManager()

def ensure_data_dir(file_path):
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def read_json_file(file_path, default=None):
    if default is None:
        default = {}
    
    # Check SQL first
    key = os.path.basename(file_path).replace('.json', '')
    data = db.get_kv(key)
    if data is not None:
        return data
        
    # Fallback to file for safety or during transition
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return default

def write_json_with_backup(data, file_path):
    # Write to SQL (Master)
    key = os.path.basename(file_path).replace('.json', '')
    db.set_kv(key, data)
    
    # Optional: Still write to JSON for frontend bundle compatibility if needed, 
    # but we want to eventually stop this. For now keep it as a sync.
    ensure_data_dir(file_path)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def normalize_map_name(requested_map, existing_maps):
    if not existing_maps:
        return requested_map
    if requested_map in existing_maps:
        return requested_map
    
    lower_requested = requested_map.lower().strip()
    
    # Case-insensitive match
    for existing in existing_maps:
        if existing.lower() == lower_requested:
            return existing
            
    # Substring matches
    for existing in existing_maps:
        lower_existing = existing.lower()
        if lower_requested in lower_existing and len(lower_requested) > 3:
            return existing
        if lower_existing in lower_requested and len(lower_existing) > 3:
            return existing
            
    # Word based match
    requested_words = lower_requested.split()
    if requested_words and len(requested_words[0]) > 3:
        first_word = requested_words[0]
        for existing in existing_maps:
            lower_existing = existing.lower()
            existing_words = lower_existing.split()
            if existing_words and existing_words[0] == first_word:
                return existing
            if lower_existing.startswith(first_word + ' '):
                return existing
                
    return None

# --- Constraints API ---
@war_room_bp.route('/roster-constraints', methods=['GET'])
def get_constraints():
    config = read_json_file(CONFIG_FILE, {})
    data = config.get('roster_constraints', {"global_bans": [], "global_priorities": [], "role_preferences": {}})
    return jsonify(data)

@war_room_bp.route('/roster-constraints', methods=['POST'])
def update_constraints():
    try:
        config = read_json_file(CONFIG_FILE, {})
        current = config.get('roster_constraints', {"global_bans": [], "global_priorities": [], "role_preferences": {}})
        update = request.json or {}
        
        action = update.get('action')
        hero = update.get('hero')
        remove = update.get('remove', False)
        
        if not action or not hero:
            return jsonify({"error": "Missing action or hero"}), 400
            
        if action == 'ban':
            if remove:
                current['global_bans'] = [h for h in current.get('global_bans', []) if h != hero]
            elif hero not in current.get('global_bans', []):
                current.setdefault('global_bans', []).append(hero)
                current['global_priorities'] = [h for h in current.get('global_priorities', []) if h != hero]
        elif action == 'priority':
            if remove:
                current['global_priorities'] = [h for h in current.get('global_priorities', []) if h != hero]
            elif hero not in current.get('global_priorities', []):
                current.setdefault('global_priorities', []).append(hero)
                current['global_bans'] = [h for h in current.get('global_bans', []) if h != hero]
        
        config['roster_constraints'] = current
        write_json_with_backup(config, CONFIG_FILE)
        return jsonify({"success": True, "data": current})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Strategies API ---
@war_room_bp.route('/strategies', methods=['GET'])
def get_strategies():
    config = read_json_file(CONFIG_FILE, {})
    data = config.get('strategies', {})
    return jsonify(data)

@war_room_bp.route('/strategies', methods=['POST'])
def update_strategies():
    try:
        update = request.json or {}
        if not update.get('action') or not update.get('map'):
            return jsonify({"error": "Missing action or map"}), 400
            
        config = read_json_file(CONFIG_FILE, {})
        strategies = config.get('strategies', {})
        existing_maps = list(strategies.keys())
        
        normalized_map = normalize_map_name(update['map'], existing_maps)
        if not normalized_map:
            # Create new map if not found and action is update_rules
            normalized_map = update['map']
            
        map_data = strategies.setdefault(normalized_map, {})
        map_data.setdefault('rules', [])
        
        action = update['action']
        data = update.get('data', {})
        
        if action == 'update_rules':
            rule_content = data.get('rule')
            if not rule_content:
                return jsonify({"error": "Missing rule content"}), 400
            
            new_rule = {
                "id": str(int(datetime.now().timestamp() * 1000)),
                "content": rule_content,
                "type": data.get('type', 'general'),
                "added": datetime.utcnow().isoformat() + 'Z'
            }
            map_data['rules'].append(new_rule)
            
        elif action == 'update_primary':
            primary = map_data.setdefault('primary', {})
            primary.update(data)
            if update.get('desc'):
                map_data['desc'] = update['desc']
                
        elif action == 'update_backup':
            backups = map_data.setdefault('backups', [])
            hero_name_lower = data.get('name', '').lower()
            existing_idx = next((i for i, b in enumerate(backups) if b.get('name', '').lower() == hero_name_lower), -1)
            
            if existing_idx >= 0:
                backups[existing_idx].update(data)
            else:
                backups.append(data)
                
        elif action == 'remove_backup':
            backups = map_data.get('backups', [])
            hero_name_lower = data.get('name', '').lower()
            map_data['backups'] = [b for b in backups if b.get('name', '').lower() != hero_name_lower]
        else:
            return jsonify({"error": f"Unknown action: {action}"}), 400
            
        config['strategies'] = strategies
        write_json_with_backup(config, CONFIG_FILE)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Stats API ---
@war_room_bp.route('/stats', methods=['POST'])
def update_stats():
    try:
        update = request.json or {}
        hero_name = update.get('hero')
        if not hero_name:
            return jsonify({"error": "Missing hero"}), 400
            
        stats = read_json_file(HERO_STATS_FILE, {"data": [], "metadata": {}})
        heroes = stats.setdefault('data', [])
        
        hero_idx = next((i for i, h in enumerate(heroes) if h.get('hero') == hero_name), -1)
        
        if hero_idx >= 0:
            heroes[hero_idx].update(update)
            heroes[hero_idx]['hero'] = hero_name # Persist name
        else:
            heroes.append({
                "hero": hero_name,
                "wins": update.get('wins', 0),
                "losses": update.get('losses', 0),
                "games_played": update.get('wins', 0) + update.get('losses', 0),
                "win_rate": update.get('win_rate', 0),
                "mmr": update.get('mmr', 0)
            })
            
        # Recalculate WR
        hero = next(h for h in heroes if h.get('hero') == hero_name)
        if hero.get('games_played', 0) > 0:
            hero['win_rate'] = round((hero['wins'] / hero['games_played']) * 100, 1)
            
        write_json_with_backup(stats, HERO_STATS_FILE)
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Logging API ---
@war_room_bp.route('/logs', methods=['POST'])
def add_log():
    try:
        data = request.json or {}
        os.makedirs(LOGS_DIR, exist_ok=True)
        log_file = os.path.join(LOGS_DIR, 'chat_errors.json')
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "type": data.get('type', 'ERROR'),
            "message": data.get('message'),
            "context": data.get('context', {})
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
