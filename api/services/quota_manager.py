"""
Quota Manager
Tracks and enforces API usage limits to prevent quota exhaustion
"""

import json
import time
from pathlib import Path

class QuotaManager:
    """Manages API quota tracking and enforcement"""
    
    QUOTA_FILE = ".api_quota.json"
    
    # FREE TIER LIMITS (Google AI Pro Plan Tier 1)
    # These are the FREE allotment limits - staying within these = $0 cost
    DAILY_LIMITS = {
        "gemini-2.5-flash": 1500,     # Free tier RPD
        "gemini-2.5-flash-lite": 1500, # Free tier RPD
        "gemini-3-pro": 250,          # Free tier RPD (Legacy/Future support)
        "gemini-2.5-pro": 250,        # Free tier RPD (Legacy/Future support)
        "gemini-1.5-pro": 50,          # Free tier RPD (Lowered for stability)
        "gemini-1.5-flash": 1000,      # Free tier RPD
        "gemini-1.5-flash-002": 1000   # Legacy Support
    }
    
    # RPM (Requests Per Minute) Limits - CRITICAL for staying free
    RPM_LIMITS = {
        "gemini-2.5-flash": 15,       # Free tier: 15 RPM
        "gemini-2.5-flash-lite": 15,  # Free tier: 15 RPM
        "gemini-3-pro": 2,            # Free tier: 2 RPM
        "gemini-2.5-pro": 3,          # Free tier: 3 RPM
        "gemini-1.5-pro": 2,          # Free tier: 2 RPM
        "gemini-1.5-flash": 15,       # Free tier: 15 RPM
        "gemini-1.5-flash-002": 15    # Legacy Support
    }
    
    # Minimum seconds between requests to respect RPM
    MIN_DELAY = {
        "gemini-2.5-flash": 4,        # 60s / 15 RPM = 4s
        "gemini-2.5-flash-lite": 4,   # 60s / 15 RPM = 4s
        "gemini-3-pro": 30,           # 60s / 2 RPM = 30s
        "gemini-2.5-pro": 20,         # 60s / 3 RPM = 20s
        "gemini-1.5-pro": 30,         # 60s / 2 RPM = 30s
        "gemini-1.5-flash": 4,        # 60s / 15 RPM = 4s
        "gemini-1.5-flash-002": 4     # Legacy Support
    }
    
    def __init__(self):
        self.quota_data = self._load_quota()
    
    def _load_quota(self):
        """Load quota data from file"""
        if Path(self.QUOTA_FILE).exists():
            try:
                with open(self.QUOTA_FILE, 'r') as f:
                    data = json.load(f)
                    
                    # Reset if it's a new day
                    last_reset = data.get('last_reset', 0)
                    current_day = time.strftime('%Y-%m-%d')
                    last_day = time.strftime('%Y-%m-%d', time.localtime(last_reset))
                    
                    if current_day != last_day:
                        return self._create_fresh_quota()
                    
                    return data
            except:
                pass
        
        return self._create_fresh_quota()
    
    def _create_fresh_quota(self):
        """Create fresh quota tracking"""
        return {
            'last_reset': time.time(),
            'reset_date': time.strftime('%Y-%m-%d'),
            'usage': {
                'gemini-2.5-flash': 0,
                'gemini-2.5-flash-lite': 0,
                'gemini-3-pro': 0,
                'gemini-2.5-pro': 0,
                'gemini-1.5-pro': 0,
                'gemini-1.5-flash': 0,
                'gemini-1.5-flash-002': 0
            }
        }
    
    def _save_quota(self):
        """Save quota data to file"""
        try:
            with open(self.QUOTA_FILE, 'w') as f:
                json.dump(self.quota_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save quota data: {e}")
    
    def can_make_request(self, model="gemini-2.5-flash"):
        """Check if we can make another API request"""
        current_usage = self.quota_data['usage'].get(model, 0)
        limit = self.DAILY_LIMITS.get(model, 100)
        
        return current_usage < limit
    
    def record_request(self, model="gemini-2.5-flash"):
        """Record an API request"""
        if model not in self.quota_data['usage']:
            self.quota_data['usage'][model] = 0
        
        self.quota_data['usage'][model] += 1
        self._save_quota()
    
    def get_remaining(self, model="gemini-2.5-flash"):
        """Get remaining requests for a model"""
        current_usage = self.quota_data['usage'].get(model, 0)
        limit = self.DAILY_LIMITS.get(model, 100)
        return max(0, limit - current_usage)

    def get_status(self):
        """Get full quota status for all models"""
        status = {}
        for model in self.DAILY_LIMITS:
            current = self.quota_data['usage'].get(model, 0)
            limit = self.DAILY_LIMITS[model]
            status[model] = {
                'used': current,
                'limit': limit,
                'remaining': max(0, limit - current),
                'percent': round((current / limit * 100), 1) if limit > 0 else 0
            }
        return status

    def can_process_replay(self):
        """Allow replay processing (separate from AI quota for now)"""
        return True
