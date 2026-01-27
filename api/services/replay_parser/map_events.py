def handle_stat_game_event(event, stats_data, players):
    ename = event.get('m_eventName', b'').decode('utf-8')
    if ename == 'JungleCampCapture':
        # ... logic ...
        pass
    elif ename == 'TownStructureDeath':
        # ... logic ...
        pass
    # and so on for all the 200 lines of map logic
    return stats_data
