"""
Quota Manager
Tracks and enforces API usage limits for high-performance models.
Customized for Nexus Command Lab's elite tier access.
"""

import json
import time
from pathlib import Path

class QuotaManager:
    """Manages API quota tracking and enforcement"""
    
    QUOTA_FILE = "api/config/quota.json"
    
    # ELITE TIER LIMITS (Daily)
    # Optimized for Gemini 3 and 3.1 access
    DAILY_LIMITS = {
        "gemini-3.1-pro-preview": 250,        
        "gemini-3-pro-preview": 250,
        "gemini-3-flash-preview": 1000,
        "gemini-2.5-flash": 1500,     
        "gemini-2.0-flash": 1500,
        "gemini-1.5-pro": 50,          
        "gemini-1.5-flash": 1500      
    }
    
    # RPM Limits (Optimized for performance)
    RPM_LIMITS = {
        "gemini-3.1-pro-preview": 5,          
        "gemini-3-pro-preview": 5,
        "gemini-3-flash-preview": 15,
        "gemini-2.5-flash": 15,
        "gemini-2.0-flash": 15,
        "gemini-1.5-pro": 2,          
        "gemini-1.5-flash": 15       
    }
    
    # Minimum seconds between requests
    MIN_DELAY = {
        "gemini-3.1-pro-preview": 12,
        "gemini-3-pro-preview": 12,
        "gemini-3-flash-preview": 4,
        "gemini-2.5-flash": 4,
        "gemini-2.0-flash": 4,
        "gemini-1.5-pro": 30,         
        "gemini-1.5-flash": 4        
    }
    
    def __init__(self):
        self.quota_data = self._load_quota()
    
    def _load_quota(self):
        """Load quota data from file"""
        if Path(self.QUOTA_FILE).exists():
            try:
                with open(self.QUOTA_FILE, 'r') as f:
                    data = json.load(f)
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
            'usage': {model: 0 for model in self.DAILY_LIMITS}
        }
    
    def _save_quota(self):
        """Save quota data to file"""
        try:
            Path(self.QUOTA_FILE).parent.mkdir(parents=True, exist_ok=True)
            with open(self.QUOTA_FILE, 'w') as f:
                json.dump(self.quota_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save quota data: {e}")
    
    def can_make_request(self, model="gemini-3-flash-preview"):
        """Check if we can make another API request"""
        current_usage = self.quota_data['usage'].get(model, 0)
        limit = self.DAILY_LIMITS.get(model, 1000)
        return current_usage < limit
    
    def record_request(self, model="gemini-3-flash-preview"):
        """Record an API request"""
        if model not in self.quota_data['usage']:
            self.quota_data['usage'][model] = 0
        self.quota_data['usage'][model] += 1
        self._save_quota()
    
    def get_remaining(self, model="gemini-3-flash-preview"):
        """Get remaining requests for a model"""
        current_usage = self.quota_data['usage'].get(model, 0)
        limit = self.DAILY_LIMITS.get(model, 1000)
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
