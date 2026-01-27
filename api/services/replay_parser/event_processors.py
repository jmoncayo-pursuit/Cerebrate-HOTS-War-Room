import unicodedata
from .talents import get_talent_from_index, TALENTS_DB

def handle_unit_born(event, unit_tags):
    tag = event.get('m_unitTagIndex')
    if tag is not None:
        u_type = event.get('m_unitTypeName', b'').decode('utf-8') if isinstance(event.get('m_unitTypeName'), bytes) else str(event.get('m_unitTypeName', ''))
        u_pid = event.get('m_controlPlayerId', event.get('m_upkeepPlayerId'))
        unit_tags[tag] = {'type': u_type, 'pid': u_pid}
        boss_keywords = ['Boss', 'GraveyardBoss', 'ArchangelSiege', 'WebweaverQueen', 'SlimeBoss']
        if any(kw in u_type for kw in boss_keywords) and u_pid is None:
            unit_tags[tag]['is_boss'] = True

def handle_hero_banned(event, players):
    team_id = event.get('m_controllingTeam')
    if team_id is None:
        user_wrapper = event.get('_userid', {})
        if isinstance(user_wrapper, dict):
            uid = user_wrapper.get('m_userId')
            if uid is not None and 0 <= uid < len(players):
                team_id = players[uid]['team']
    return {
        'hero': event.get('m_hero', b'').decode('utf-8'),
        'gameloop': event['_gameloop'],
        'team': team_id
    }

def handle_talent_chosen(event, players, stats_data):
    pid = event.get('m_controlPlayerId') or event.get('m_userid')
    if pid is not None and pid in stats_data:
        idx = event.get('m_talentNameIndex')
        rich_id = None
        if idx is not None:
            player_idx = pid - 1
            if 0 <= player_idx < len(players):
                hero_n = players[player_idx]['hero']
                rich_id = get_talent_from_index(hero_n, idx, TALENTS_DB)
                if rich_id and any(g in rich_id for g in ['Vehicle', 'Mount', 'Hearthstone', 'Spray', 'Voice', 'Banner']):
                    return None
        return {
            "timestamp": round(event['_gameloop'] / 16.0, 1),
            "talent_index": idx,
            "talent_name": rich_id if rich_id else f"Talent Index {idx}",
            "source": "tracker_legacy"
        }
    return None

def handle_stat_game_event(event, players, stats_data, active_boss_engagements):
    ename = event.get('m_eventName', b'').decode('utf-8')
    if ename == 'JungleCampCapture':
        # ... logic ...
        pass
    # This function would contain most of the SStatGameEvent logic.
    # To keep it manageable, one could further split by event name.
    pass
