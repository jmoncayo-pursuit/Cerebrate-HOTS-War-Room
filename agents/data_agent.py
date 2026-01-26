"""
Data Management Agent
Specializes in data integrity, ingestion monitoring, and context preparation for the swarm.
"""

from .base_agent import BaseAgent
import json

class DataAgent(BaseAgent):
    """Agent specialized in database health, ingestion status, and data dissemination readiness"""
    
    def __init__(self, db_manager=None, call_gemini_fn=None):
        super().__init__(
            name="QUARTERMASTER",
            role="Data & Logistics Specialist",
            expertise=[
                "Data Integrity Monitoring",
                "Ingestion Pipeline Oversight",
                "Database Health Audit",
                "Context Normalization",
                "Dissemination Protocol"
            ],
            call_gemini_fn=call_gemini_fn
        )
        self.db = db_manager
    
    def can_handle(self, query, context):
        """Check if query is about data, logs, database, or system health"""
        query_lower = query.lower()
        
        data_keywords = [
            'database', 'data', 'replays', 'ingestion', 'status', 
            'sync', 'synchronized', 'health', 'storage', 'integrity',
            'missing data', 'where is my', 'update', 'records', 'logs',
            'provenance', 'source', 'disseminate', 'prepare context'
        ]
        
        return any(keyword in query_lower for keyword in data_keywords)
    
    def analyze(self, query, context):
        """
        Perform data audit or ingestion check.
        """
        # Fetch actual system stats for the agent to reason with
        stats = self._get_system_stats()
        
        prompt = f"""You are the Cerebrate QUARTERMASTER (Data Management Agent).
Your purpose is to ensure all tactical data is structuraly sound, verified, and ready for dissemination to other agents (Analyst, Scout, etc.).

**SYSTEM STATS INPUT (LIVE):**
{json.dumps(stats, indent=2)}

**QUERY:**
{query}

**MISSION OBJECTIVE:**
Evaluate the health of the tactical database and the reliability of the recent ingestion.
If the user asks about data status, respond with high-fidelity technical assessment.
Explain if the data is "Dissemination Ready" or if there are "Synchronization Gaps".

**FORMATTING:**
Use a "LOGISTICS REPORT" format.
Sections:
- [STATUS] (OPERATIONAL / DEGRADED / SYNCING)
- [INTEGRITY CHECK] (Brief technical audit of the records)
- [INGESTION ALERT] (Recent replay ingestion status)
- [DIRECTIVE] (What the commander or other agents should know)
"""

        try:
            if self.call_gemini_fn:
                response_text = self.call_gemini_fn(prompt, raw_mode=True, silent=True)
                
                return {
                    'agent': self.name,
                    'success': True,
                    'analysis_type': 'data_audit',
                    'query': query,
                    'response': response_text,
                    'system_stats': stats
                }
            else:
                return {
                    'agent': self.name,
                    'success': False,
                    'error': "Neural link for Quartermaster offline.",
                    'response': "UNABLE TO AUDIT: Neural link missing. System stats indicate operational readiness but logic core is detached."
                }
        except Exception as e:
            return {
                'agent': self.name,
                'success': False,
                'error': str(e),
                'response': f"Quartermaster data scan failed: {str(e)}"
            }

    def _get_system_stats(self):
        """Gather real metrics from the DB and environment"""
        stats = {
            "total_matches": 0,
            "total_players": 0,
            "last_ingestion": "None",
            "health_score": 1.0
        }
        
        if self.db:
            try:
                # Get match count
                with self.db._get_connection() as conn:
                    stats["total_matches"] = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
                    stats["total_players"] = conn.execute("SELECT COUNT(DISTINCT name) FROM match_players").fetchone()[0]
                    
                    # Get last ingestion time
                    last_match = conn.execute("SELECT date FROM matches ORDER BY date DESC LIMIT 1").fetchone()
                    if last_match:
                        stats["last_ingestion"] = last_match[0]
                        
                stats["health_score"] = 1.0 if stats["total_matches"] > 0 else 0.5
            except Exception as e:
                stats["error"] = str(e)
                stats["health_score"] = 0.0
                
        return stats

    def get_example_queries(self):
        return [
            "Check database health",
            "Is my latest replay processed?",
            "Are my stats synchronized?",
            "Verify data integrity for dissemination",
            "How many matches are in the system?"
        ]
