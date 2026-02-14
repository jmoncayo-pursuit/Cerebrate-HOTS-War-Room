"""
Hooks Manager for Cerebrate AI Agent
Inspired by Gemini CLI hooks - allows custom logic injection at key points
"""

import re
from typing import Callable, Dict, List, Any, Optional
from api.logger import ColoredLogger


class HookResponse:
    """Structured response from a hook"""
    ALLOW = "allow"
    DENY = "deny"
    MODIFY = "modify"
    SKIP = "skip"
    
    def __init__(self, decision: str, reason: str = "", modified_data: Any = None, 
                 cached_result: Any = None, system_message: str = ""):
        self.decision = decision
        self.reason = reason
        self.modified_data = modified_data
        self.cached_result = cached_result
        self.system_message = system_message
    
    @staticmethod
    def allow(reason: str = ""):
        return HookResponse(HookResponse.ALLOW, reason)
    
    @staticmethod
    def deny(reason: str, system_message: str = ""):
        return HookResponse(HookResponse.DENY, reason, system_message=system_message)
    
    @staticmethod
    def modify(modified_data: Any, reason: str = ""):
        return HookResponse(HookResponse.MODIFY, reason, modified_data=modified_data)
    
    @staticmethod
    def skip(cached_result: Any, reason: str = ""):
        return HookResponse(HookResponse.SKIP, reason, cached_result=cached_result)


class Hook:
    """Represents a single hook"""
    def __init__(self, name: str, hook_fn: Callable, matcher: Optional[str] = None, 
                 enabled: bool = True, max_retries: int = 0):
        self.name = name
        self.hook_fn = hook_fn
        self.matcher = matcher  # Regex pattern to match against data
        self.enabled = enabled
        self.max_retries = max_retries
    
    def matches(self, data: Dict[str, Any]) -> bool:
        """Check if this hook should run based on matcher"""
        if not self.matcher:
            return True
        
        # Convert data to string for matching
        data_str = str(data)
        return bool(re.search(self.matcher, data_str, re.IGNORECASE))


class HooksManager:
    """
    Manages hooks for the Cerebrate AI agent
    
    Hook Events:
    - BeforeQuery: Before routing to an agent
    - AfterQuery: After agent responds
    - BeforeAnalysis: Before generating match summary
    - AfterAnalysis: After summary is generated
    """
    
    def __init__(self):
        self.hooks: Dict[str, List[Hook]] = {
            'BeforeQuery': [],
            'AfterQuery': [],
            'BeforeAnalysis': [],
            'AfterAnalysis': []
        }
        ColoredLogger.info("Hooks manager initialized", "HOOKS")
    
    def register_hook(self, event_type: str, name: str, hook_fn: Callable, 
                     matcher: Optional[str] = None, enabled: bool = True, 
                     max_retries: int = 0):
        """
        Register a hook for a specific event
        
        Args:
            event_type: One of BeforeQuery, AfterQuery, BeforeAnalysis, AfterAnalysis
            name: Unique name for this hook
            hook_fn: Function to execute (receives data dict, returns HookResponse)
            matcher: Optional regex pattern to filter when hook runs
            enabled: Whether hook is active
            max_retries: Max retry attempts if hook denies (AfterAnalysis only)
        """
        if event_type not in self.hooks:
            raise ValueError(f"Invalid event type: {event_type}")
        
        hook = Hook(name, hook_fn, matcher, enabled, max_retries)
        self.hooks[event_type].append(hook)
        ColoredLogger.success(f"Registered hook: {name} for {event_type}", "HOOKS")
    
    def execute_hooks(self, event_type: str, data: Dict[str, Any]) -> HookResponse:
        """
        Execute all hooks for a given event type
        
        Args:
            event_type: Event to trigger
            data: Data to pass to hooks
        
        Returns:
            HookResponse: Combined result from all hooks
        """
        if event_type not in self.hooks:
            return HookResponse.allow()
        
        hooks = self.hooks[event_type]
        if not hooks:
            return HookResponse.allow()
        
        ColoredLogger.info(f"Executing {len(hooks)} hook(s) for {event_type}", "HOOKS")
        
        current_data = data
        for hook in hooks:
            if not hook.enabled:
                continue
            
            if not hook.matches(current_data):
                # Skip hooks that don't match
                continue
            
            try:
                response = hook.hook_fn(current_data)
                
                if response.decision == HookResponse.DENY:
                    ColoredLogger.warn(
                        f"Hook {hook.name} DENIED: {response.reason}", "HOOKS"
                    )
                    return response
                
                elif response.decision == HookResponse.SKIP:
                    ColoredLogger.info(
                        f"Hook {hook.name} SKIP: {response.reason}", "HOOKS"
                    )
                    return response
                
                elif response.decision == HookResponse.MODIFY:
                    ColoredLogger.info(
                        f"Hook {hook.name} MODIFIED: {response.reason}", "HOOKS"
                    )
                    current_data = response.modified_data
                
                else:  # ALLOW
                    ColoredLogger.success(
                        f"Hook {hook.name} PASSED{': ' + response.reason if response.reason else ''}", 
                        "HOOKS"
                    )
            
            except Exception as e:
                ColoredLogger.error(f"Hook {hook.name} failed: {str(e)}", "HOOKS")
                # Continue with other hooks on error
                continue
        
        # If we modified data, return it
        if current_data != data:
            return HookResponse.modify(current_data, "Data modified by hooks")
        
        return HookResponse.allow("All hooks passed")
    
    def get_hook_status(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get status of all registered hooks"""
        status = {}
        for event_type, hooks in self.hooks.items():
            status[event_type] = [
                {
                    'name': hook.name,
                    'enabled': hook.enabled,
                    'matcher': hook.matcher,
                    'max_retries': hook.max_retries
                }
                for hook in hooks
            ]
        return status
