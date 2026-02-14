"""
Cache Manager Hook
BeforeAnalysis hook that checks for cached analysis
"""

import hashlib
import json
from typing import Dict, Any
from agents.hooks_manager import HookResponse


# Simple in-memory cache (could be replaced with Redis/database)
_analysis_cache = {}


def cache_manager_hook(data: Dict[str, Any]) -> HookResponse:
    """
    Check cache for identical match analysis
    
    Args:
        data: Contains match_data
    
    Returns:
        HookResponse: skip with cached result if found
    """
    match_data = data.get('match_data', {})
    
    # Create cache key from match essentials
    cache_key_data = {
        'map': match_data.get('map'),
        'hero': match_data.get('hero'),
        'result': match_data.get('result'),
        'duration': match_data.get('duration'),
        'match_id': match_data.get('id')  # Use match ID for exact match
    }
    
    # Generate hash
    cache_key = hashlib.md5(
        json.dumps(cache_key_data, sort_keys=True).encode()
    ).hexdigest()
    
    # Check cache (only if not forcing)
    is_force = data.get('force', False)
    if not is_force and cache_key in _analysis_cache:
        cached_analysis = _analysis_cache[cache_key]
        return HookResponse.skip(
            cached_analysis,
            f"Cache hit for match {match_data.get('id', 'unknown')}"
        )
    
    # Store cache key in data for later storage
    modified_data = data.copy()
    modified_data['_cache_key'] = cache_key
    
    return HookResponse.modify(
        modified_data,
        "Cache miss - will cache after analysis"
    )


def store_in_cache(cache_key: str, analysis: Dict[str, Any]):
    """Store analysis in cache"""
    _analysis_cache[cache_key] = analysis


def clear_cache():
    """Clear all cached analyses"""
    global _analysis_cache
    _analysis_cache = {}
