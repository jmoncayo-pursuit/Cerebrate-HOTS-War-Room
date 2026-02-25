"""
Base Agent Class
Foundation for all specialized Nexus agents
"""

class BaseAgent:
    """Base class for all specialized agents in the Nexus system"""
    
    def __init__(self, name, role, expertise, call_gemini_fn=None):
        """
        Initialize a base agent
        
        Args:
            name: Agent identifier (e.g., "ANALYST", "SCOUT")
            role: Human-readable role description
            expertise: List of domains this agent handles
            call_gemini_fn: Injected Gemini API function to avoid circular imports
        """
        self.name = name
        self.role = role
        self.expertise = expertise if isinstance(expertise, list) else [expertise]
        self.call_gemini_fn = call_gemini_fn
    
    def can_handle(self, query, context):
        """
        Determine if this agent can handle the given query
        
        Args:
            query: User's question/request
            context: Additional context (profile, matches, etc.)
        
        Returns:
            bool: True if this agent should handle the query
        """
        raise NotImplementedError(f"{self.name} must implement can_handle()")
    
    def analyze(self, query, context):
        """
        Perform agent-specific analysis
        
        Args:
            query: User's question/request
            context: Additional context
        
        Returns:
            dict: Agent's response with analysis
        """
        raise NotImplementedError(f"{self.name} must implement analyze()")
    
    def get_capabilities(self):
        """
        Return agent's capabilities for discovery
        
        Returns:
            dict: Agent metadata
        """
        return {
            'name': self.name,
            'role': self.role,
            'expertise': self.expertise,
            'example_queries': self.get_example_queries()
        }
    
    def get_example_queries(self):
        """
        Return example queries this agent can handle
        
        Returns:
            list: Example user queries
        """
        return []
        
    def get_identity(self):
        """
        Return agent identity metadata
        
        Returns:
            dict: Agent identity
        """
        return {
            'name': self.name,
            'role': self.role,
            'expertise': self.expertise
        }
