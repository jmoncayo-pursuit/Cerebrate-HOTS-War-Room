import os
import json
import uuid
import google.generativeai as genai
from datetime import datetime
from api.logger import ColoredLogger
from api.services.database import DatabaseManager

from api.agentic_brain import AgenticBrain

class IntelligenceService:
    """Consolidated service for AI interaction, advice history, and temporal telemetry."""
    
    # --- NEURAL TIERING CONFIG ---
    TIERS = {
        "REASONING": "gemini-2.5-flash", 
        "SENSING": "gemini-2.5-flash",  
        "CHAT": "gemini-2.5-flash"      
    }

    def __init__(self, db_manager=None, api_key=None):
        self.db = db_manager or DatabaseManager()
        self.brain = AgenticBrain()
        from api.services.mcp_bridge_service import mcp_bridge
        self.mcp = mcp_bridge
        self.quota = None
        try:
            from quota_manager import QuotaManager
            self.quota = QuotaManager()
        except ImportError:
            pass

        if api_key:
            genai.configure(api_key=api_key)
            
            # Load System Protocol
            protocol_path = os.path.join(os.path.dirname(__file__), '..', '..', '.agent', 'brain', 'AI_CHAT_PROTOCOL.md')
            system_instruction = "You are the Cerebrate Intelligence."
            if os.path.exists(protocol_path):
                with open(protocol_path, 'r') as f:
                    system_instruction = f.read()
            
            # Default model for general tasks
            self.model = genai.GenerativeModel(
                model_name=self.TIERS["CHAT"],
                system_instruction=system_instruction
            )
        else:
            self.model = None

    def _get_model_for_tier(self, tier):
        """Lazy load or return model for a specific tier."""
        model_name = self.TIERS.get(tier, self.TIERS["CHAT"])
        
        # PRO TALLY ALERT LOGIC
        if "pro" in model_name.lower() and self.quota:
            status = self.quota.get_status().get(model_name, {})
            used = status.get('used', 0)
            limit = status.get('limit', 0)
            ColoredLogger.warn(f"⚠️ NEURAL ALERT: Using PRO Model [{model_name}]. Daily Tally: {used+1}/{limit}", "INTEL")
        
        return genai.GenerativeModel(model_name=model_name)

    # --- CHAT & AI LOGIC ---
    def generate_chat_response(self, message, history=None, tier="CHAT"):
        if not self.model: return "AI Not Initialized"
        try:
            # 1. Select the appropriate Tier
            active_model = self._get_model_for_tier(tier)
            
            # 2. Agentic Pre-Computation
            dossier = self.brain.process_request(message)
            
            # 3. Inject Dossier into Prompt
            full_prompt = f"{dossier}\n\nUSER QUERY: {message}"
            
            chat = active_model.start_chat(history=history or [])
            response = chat.send_message(full_prompt)
            
            # 4. Record Quota
            if self.quota:
                self.quota.record_request(active_model.model_name)
                
            return response.text
        except Exception as e:
            ColoredLogger.error(f"Generate Error: {e}")
            return f"Error: {str(e)}"
        except Exception as e:
            ColoredLogger.error(f"Generate Error: {e}")
            return f"Error: {str(e)}"

    # --- ADVICE & EFFECTIVENESS ---
    def log_advice(self, context, advice_text):
        log = self.db.get_kv('advice_log') or {"advice_history": []}
        adv_id = f"adv_{uuid.uuid4().hex[:8]}"
        entry = {
            "id": adv_id,
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "advice": advice_text,
            "outcome": None
        }
        log['advice_history'].insert(0, entry)
        self.db.set_kv('advice_log', log)
        return adv_id

    def get_advice_stats(self):
        log = self.db.get_kv('advice_log') or {"advice_history": []}
        history = log.get('advice_history', [])
        return {
            "total_given": len(history),
            "recent": history[:10]
        }

    # --- TELEMETRY & PATTERNS ---
    def get_temporal_patterns(self):
        """Aggregate win rates by time of day (EST)."""
        matches = self.db.get_matches(limit=1000)
        buckets = {
            'morning': {'wins': 0, 'games': 0},   # 06-12
            'afternoon': {'wins': 0, 'games': 0}, # 12-18
            'evening': {'wins': 0, 'games': 0},   # 18-00
            'night': {'wins': 0, 'games': 0}      # 00-06
        }
        for m in matches:
            try:
                dt = datetime.fromisoformat(m['date'])
                hour = (dt.hour - 5) % 24
                key = 'morning' if 6 <= hour < 12 else 'afternoon' if 12 <= hour < 18 else 'evening' if 18 <= hour < 24 else 'night'
                buckets[key]['games'] += 1
                if m['result'] == 'WIN': buckets[key]['wins'] += 1
            except: continue
        return buckets
