import os
import json
import uuid
import google.generativeai as genai
import time
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
            
            # Load and store System Protocol for all tiers
            protocol_path = os.path.join(os.path.dirname(__file__), '..', '..', '.agent', 'brain', 'AI_CHAT_PROTOCOL.md')
            self.system_instruction = "You are the Cerebrate Intelligence."
            if os.path.exists(protocol_path):
                with open(protocol_path, 'r') as f:
                    self.system_instruction = f.read()
            
            # Default model for general tasks
            self.model = self._get_model_for_tier("CHAT")
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
        
        return genai.GenerativeModel(
            model_name=model_name,
            system_instruction=getattr(self, 'system_instruction', "You are the Cerebrate Intelligence.")
        )

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
            
            # 4. Record Telemetry & Quota
            try:
                # Extract tokens
                usage = getattr(response, 'usage_metadata', None)
                p_tokens = usage.prompt_token_count if usage else 0
                r_tokens = usage.candidates_token_count if usage else 0
                t_tokens = usage.total_token_count if usage else 0
                
                # Update KV Telemetry
                telemetry = self.db.get_kv('token_telemetry') or {
                    "total_tokens": 0, "prompt_tokens": 0, "response_tokens": 0, "total_calls": 0, "history": []
                }
                
                telemetry["total_tokens"] += t_tokens
                telemetry["prompt_tokens"] += p_tokens
                telemetry["response_tokens"] += r_tokens
                telemetry["total_calls"] += 1
                
                # Add to history (limit to 20)
                telemetry["history"].insert(0, {
                    "timestamp": time.time() if 'time' in globals() else datetime.now().timestamp(),
                    "prompt_t": p_tokens,
                    "resp_t": r_tokens,
                    "total_t": t_tokens,
                    "model": active_model.model_name
                })
                telemetry["history"] = telemetry["history"][:20]
                
                self.db.set_kv('token_telemetry', telemetry)
            except Exception as tel_e:
                ColoredLogger.error(f"Telemetry Recording Error: {tel_e}")

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
