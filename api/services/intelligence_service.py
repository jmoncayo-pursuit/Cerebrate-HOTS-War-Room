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
    
    def __init__(self, db_manager=None, api_key=None):
        self.db = db_manager or DatabaseManager()
        self.brain = AgenticBrain()
        if api_key:
            genai.configure(api_key=api_key)
            
            # Load System Protocol
            protocol_path = os.path.join(os.path.dirname(__file__), '..', '..', '.agent', 'brain', 'AI_CHAT_PROTOCOL.md')
            system_instruction = "You are the Cerebrate Intelligence."
            if os.path.exists(protocol_path):
                with open(protocol_path, 'r') as f:
                    system_instruction = f.read()
            
            self.model = genai.GenerativeModel(
                model_name='gemini-1.5-flash-latest',
                system_instruction=system_instruction
            )
        else:
            self.model = None

    # --- CHAT & AI LOGIC ---
    def generate_chat_response(self, message, history=None):
        if not self.model: return "AI Not Initialized"
        try:
            # 1. Agentic Pre-Computation
            dossier = self.brain.process_request(message)
            
            # 2. Inject Dossier into Prompt (Hidden from user UI, visible to LLM)
            full_prompt = f"{dossier}\n\nUSER QUERY: {message}"
            
            chat = self.model.start_chat(history=history or [])
            response = chat.send_message(full_prompt)
            return response.text
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
