"""
Nexus Orchestrator
Routes user queries to specialized agents and synthesizes responses
"""

from .analyst_agent import AnalystAgent
from .scout_agent import ScoutAgent
from .coach_agent import CoachAgent
from .tactician_agent import TacticianAgent
from .social_agent import SocialAgent
from .data_agent import DataAgent
from .map_experts.blackhearts_bay_expert import BlackheartsBayExpert
from .map_experts.cursed_hollow_expert import CursedHollowExpert
from .map_experts.infernal_shrines_expert import InfernalShrinesExpert
from .map_experts.dragon_shire_expert import DragonShireExpert
from .map_experts.warhead_junction_expert import WarheadJunctionExpert
from .map_experts.towers_of_doom_expert import TowersOfDoomExpert
from .map_experts.sky_temple_expert import SkyTempleExpert
from .map_experts.battlefield_of_eternity_expert import BattlefieldOfEternityExpert
from .map_experts.tomb_of_the_spider_queen_expert import TombOfTheSpiderQueenExpert
from .map_experts.volskaya_foundry_expert import VolskayaFoundryExpert
from .map_experts.alterac_pass_expert import AlteracPassExpert
from .map_experts.braxis_holdout_expert import BraxisHoldoutExpert
from .map_experts.hanamura_temple_expert import HanamuraTempleExpert
from .map_experts.garden_of_terror_expert import GardenOfTerrorExpert

class NexusOrchestrator:
    """
    Main orchestrator that routes queries to specialized agents
    """
    
    def __init__(self, call_gemini_api_fn=None, db_manager=None, call_gemini_fn=None):
        """
        Initialize orchestrator with available agents
        
        Args:
            call_gemini_api_fn: Gemini API function for agents to use
            db_manager: Database manager for data access
            call_gemini_fn: Alias for call_gemini_api_fn (backwards compat)
        """
        fn = call_gemini_api_fn or call_gemini_fn
        self.call_gemini_fn = fn
        self.db = db_manager
        
        # Initialize map experts (prioritized for map-specific queries)
        self.map_experts = {
            "Blackheart's Bay": BlackheartsBayExpert(call_gemini_api_fn=fn, db_manager=db_manager),
            "Cursed Hollow": CursedHollowExpert(call_gemini_api_fn=fn, db_manager=db_manager),
            "Infernal Shrines": InfernalShrinesExpert(call_gemini_api_fn=fn, db_manager=db_manager),
            "Dragon Shire": DragonShireExpert(call_gemini_api_fn=fn, db_manager=db_manager),
            "Warhead Junction": WarheadJunctionExpert(call_gemini_api_fn=fn, db_manager=db_manager),
            "Towers of Doom": TowersOfDoomExpert(call_gemini_api_fn=fn, db_manager=db_manager),
            "Sky Temple": SkyTempleExpert(call_gemini_api_fn=fn, db_manager=db_manager),
            "Battlefield of Eternity": BattlefieldOfEternityExpert(call_gemini_api_fn=fn, db_manager=db_manager),
            "Tomb of the Spider Queen": TombOfTheSpiderQueenExpert(call_gemini_api_fn=fn, db_manager=db_manager),
            "Volskaya Foundry": VolskayaFoundryExpert(call_gemini_api_fn=fn, db_manager=db_manager),
            "Alterac Pass": AlteracPassExpert(call_gemini_api_fn=fn, db_manager=db_manager),
            "Braxis Holdout": BraxisHoldoutExpert(call_gemini_api_fn=fn, db_manager=db_manager),
            "Hanamura Temple": HanamuraTempleExpert(call_gemini_api_fn=fn, db_manager=db_manager),
            "Garden of Terror": GardenOfTerrorExpert(call_gemini_api_fn=fn, db_manager=db_manager)
        }
        
        # Initialize all available agents
        self.agents = {
            'analyst': AnalystAgent(call_gemini_fn=fn),
            'scout': ScoutAgent(call_gemini_fn=fn, db_manager=db_manager),
            'coach': CoachAgent(db=db_manager, call_gemini_fn=fn),
            'tactician': TacticianAgent(db=db_manager, call_gemini_fn=fn),
            'social': SocialAgent(db=db_manager, call_gemini_fn=fn),
            'quartermaster': DataAgent(db_manager=db_manager, call_gemini_fn=fn)
        }
    
    def route_query(self, query, context):
        """
        Route user query to appropriate agent(s)
        
        Priority: Map Experts > Specialized Agents > General Agents
        
        Args:
            query: User's question/request
            context: Additional context (profile, matches, etc.)
        
        Returns:
            dict: Synthesized response from agent(s)
        """
        # 0. INJECT SHARED BRAIN DATA (Personalized Tactical Memory)
        # This allows all agents to share the same gitignored knowledge
        try:
            from api_server import load_personalized_brain
            brain_context = load_personalized_brain(context)
            context['brain_context'] = brain_context
        except ImportError:
            # Fallback if called outside api_server scope
            context['brain_context'] = ""

        # 0.5. LIVE TELEMETRY (DEPRECATED)
        # MCP Bridge integration removed per user request.
        # context['live_telemetry'] = None

        # PRIORITY 0: SYSTEM/DEBUG INTERVENTION
        # If the user is asking about the nexus link or logs, route to ANALYST immediately
        system_keywords = ['console', 'log', 'error', 'debug', 'fail', 'warning', 'nexus link', 'comm-link', 'telemetry']
        if any(w in query.lower() for w in system_keywords) and context.get('live_telemetry'):
             return self.agents['analyst'].analyze(query, context)

        # Extract entities from query for context-aware routing
        context['map'] = self._extract_map(query)
        context['hero'] = self._extract_hero(query)
        context['player_name'] = self._extract_player(query)
        
        # PRIORITY 1: Check for map expert match
        map_name = context.get('map')
        if map_name and map_name in self.map_experts:
            map_expert = self.map_experts[map_name]
            if map_expert.can_handle(query, context):
                response = map_expert.analyze(query, context)
                response['orchestrator'] = {
                    'selected_agent': map_expert.name,
                    'capable_agents': [map_expert.name],
                    'query': query,
                    'routing_reason': f'Map expert for {map_name}'
                }
                return response
        
        # PRIORITY 2: Check specialized agents
        capable_agents = []
        for agent_name, agent in self.agents.items():
            if agent.can_handle(query, context):
                capable_agents.append((agent_name, agent))

        if not capable_agents:
            # FALLBACK: If no specific agent claimed it, default to Analyst for general Q&A
            # This ensures we never return "Unknown" for valid conversational queries
            response = self.agents['analyst'].analyze(query, context)
            response['orchestrator'] = {
                'selected_agent': 'analyst',
                'capable_agents': ['analyst'],
                'query': query,
                'routing_reason': 'Fallback to General Analyst'
            }
            return response
        
        # For now, use the first capable agent
        # TODO: In future, could call multiple agents and synthesize
        agent_name, agent = capable_agents[0]
        
        # Call the agent
        response = agent.analyze(query, context)
        
        # ELITE SYNTHESIS: Ensure every response has a human 'response' field
        if 'response' not in response or not response['response']:
             # Attempt to synthesize from data
             if 'analysis' in response and isinstance(response['analysis'], dict):
                  summary = response['analysis'].get('summary') or response['analysis'].get('win_condition')
                  if summary:
                       response['response'] = f"Tactical analysis synchronized. {summary}"
                  else:
                       response['response'] = "Data link established. Analysis complete. Review raw telemetry below."
             else:
                  response['response'] = "Mission report generated. Tactical data available."

        # Add orchestrator metadata
        response['orchestrator'] = {
            'selected_agent': agent_name,
            'capable_agents': [name for name, _ in capable_agents],
            'query': query,
            'brain_active': bool(context.get('brain_context'))
        }
        
        return response
    
    def get_available_agents(self):
        """
        Get list of all available agents and their capabilities
        
        Returns:
            list: Agent metadata
        """
        agents_list = [
            agent.get_capabilities()
            for agent in self.agents.values()
        ]
        # Add map experts
        agents_list.extend([
            expert.get_capabilities()
            for expert in self.map_experts.values()
        ])
        return agents_list
    
    def classify_query(self, query):
        """
        Classify query to determine which agent(s) should handle it
        
        Args:
            query: User's question
        
        Returns:
            dict: Classification result with agent recommendations
        """
        classifications = {}
        for agent_name, agent in self.agents.items():
            # Simple keyword-based classification for now
            # In future, could use Gemini to classify
            can_handle = agent.can_handle(query, {})
            classifications[agent_name] = {
                'can_handle': can_handle,
                'confidence': 1.0 if can_handle else 0.0
            }
        
        return {
            'query': query,
            'classifications': classifications,
            'recommended_agents': [
                name for name, info in classifications.items()
                if info['can_handle']
            ]
        }
    
    def _extract_map(self, query):
        """Extract map name from query"""
        query_lower = query.lower()
        maps = [
            'Tomb of the Spider Queen', 'Infernal Shrines', 'Dragon Shire',
            'Blackheart\'s Bay', 'Cursed Hollow', 'Sky Temple',
            'Battlefield of Eternity', 'Towers of Doom', 'Garden of Terror',
            'Volskaya Foundry', 'Braxis Holdout', 'Warhead Junction',
            'Alterac Pass', 'Hanamura Temple', 'Haunted Mines'
        ]
        
        for map_name in maps:
            if map_name.lower() in query_lower:
                return map_name
            # Check for partial matches
            map_words = map_name.lower().split()
            if len(map_words) > 1 and all(word in query_lower for word in map_words):
                return map_name
        
        return None
    
    def _extract_hero(self, query):
        """Extract hero name from query"""
        query_lower = query.lower()
        # Common hero names - could be expanded from hero_data.json
        heroes = [
            'Kharazim', 'Valla', 'Jaina', 'Muradin', 'Li-Ming',
            'Falstad', 'Sylvanas', 'Thrall', 'Raynor', 'Zagara',
            'Diablo', 'Tyrande', 'Uther', 'Rehgar', 'Brightwing',
            'Tyrael', 'Arthas', 'Illidan', 'Gazlowe', 'Kerrigan'
        ]
        
        for hero in heroes:
            if hero.lower() in query_lower:
                return hero
        
        return None
    
    def _extract_player(self, query):
        """Extract player name from query"""
        # Look for patterns like "player X" or named players
        query_lower = query.lower()
        player_keywords = ['player', 'teammate', 'ally', 'opponent', 'enemy']
        
        # Simple extraction - could be enhanced with NER
        for keyword in player_keywords:
            if keyword in query_lower:
                # Try to find name after keyword
                parts = query_lower.split(keyword)
                if len(parts) > 1:
                    # Extract potential name (simple heuristic)
                    next_part = parts[1].strip().split()[0] if parts[1].strip() else None
                    if next_part and len(next_part) > 2:
                        return next_part.capitalize()
        
        return None