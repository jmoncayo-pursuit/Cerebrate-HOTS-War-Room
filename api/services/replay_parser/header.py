import os
import hashlib
import mpyq
from heroprotocol.versions import latest

def get_match_id_from_archive(archive):
    """Generate unique match ID from MPQ header content."""
    try:
        # Most common structure
        content = archive.header.get('user_data_header', {}).get('content') or \
                  archive.header.get('user_data', {}).get('content')
        
        if not content:
            return hashlib.md5(str(os.path.getsize(archive.filename)).encode()).hexdigest()[:16]

        header = latest().decode_replay_header(content)
        id_components = [
            str(header.get('m_randomValue', '')),
            str(header.get('m_signature', '')),
            str(header.get('m_timeUTC', 0)),
            str(header.get('m_elapsedGameLoops', 0)),
            str(header.get('m_version', {}).get('m_baseBuild', 0))
        ]
        return hashlib.md5('_'.join(id_components).encode()).hexdigest()[:16]
    except:
        # Absolute fallback if header decoding fails
        return hashlib.md5(os.path.basename(archive.filename).encode()).hexdigest()[:16]

def get_match_id(replay_path):
    """Fast function to get just the match ID from a replay file."""
    try:
        if not os.path.exists(replay_path): return None
        archive = mpyq.MPQArchive(replay_path)
        return get_match_id_from_archive(archive)
    except:
        return None
