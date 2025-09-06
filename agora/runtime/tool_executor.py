"""
Agent Tool Executor: the "little orchestrator" for tool adaption and execution.

Coordinates the complete workflow of receiving tool calls, translating to platform services,
executing them and formatting responses.
"""

from typing import Dict, Any, Optional, List
from ..platform import DatabaseManager
from ..platform import services as db_services
from .action_tracker import ActionTracker
from .tool_registry import ToolRegistry, ToolDefinition


class AgentToolExecutor:
    """
    Adapter and Executor that translates semantic agent tool calls to platform service calls.
    
    This class orchestrates the complete workflow:
    1. Receive tool call from agent
    2. Translate to platform service using tool registry and action tracker
    3. Execute platform service
    4. Format response
    5. Update action tracker
    6. Return formatted response to agent
    """

    def __init__(self, db_manager: DatabaseManager, tool_registry: Optional[ToolRegistry]=None):
        self.db_manager = db_manager
        self.tool_registry = tool_registry if tool_registry else ToolRegistry()
        self._service_cache = self._build_service_cache()
        # Shared executor with per-agent action trackers
        self._agent_trackers: Dict[str, ActionTracker] = {}
    
    def _build_service_cache(self) -> Dict[str, Any]:
        """
        Build service cache dynamically from tool registry.
        
        This makes the executor independent of hardcoded services - it only loads
        the services that are actually needed by the registered tools.
        """
        
        service_cache = {}
        
        # Get all unique service names from registered tools
        service_names = set()
        for tool_def in self.tool_registry.get_all_tools().values():
            service_names.add(tool_def.service)
        
        # Dynamically import services as needed
        for service_name in service_names:
            if hasattr(db_services, service_name):
                service_cache[service_name] = getattr(db_services, service_name)
            else:
                # Allow custom services to be registered later
                service_cache[service_name] = None
        
        return service_cache
    
    def _get_agent_tracker(self, agent_username: str) -> ActionTracker:
        """
        Get or create ActionTracker for a specific agent.
        
        Args:
            agent_username: The agent's username
            
        Returns:
            ActionTracker instance for the agent
        """
        if agent_username not in self._agent_trackers:
            self._agent_trackers[agent_username] = ActionTracker()
        return self._agent_trackers[agent_username]
    
    def execute_tool_call(self, agent_username: str, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool call from an agent.
        
        Args:
            agent_username: The agent's username
            tool_call: The tool call dictionary from the agent
            
        Returns:
            Formatted response dictionary
        """
        tool_name = tool_call.get('tool')
        parameters = tool_call.get('parameters', {})
        
        # Handle nonsense/invalid tool calls gracefully
        if not tool_name or not isinstance(tool_name, str):
            return self._format_invalid_tool_response(
                tool_call, "Tool call must include a valid 'tool' field with string name"
            )
        
        if not parameters or not isinstance(parameters, dict):
            return self._format_invalid_tool_response(
                tool_call, "Tool call must include a valid 'parameters' field with dictionary"
            )
        
        # Validate agent username
        if not agent_username or not isinstance(agent_username, str):
            return self._format_invalid_tool_response(
                tool_call, "Agent username must be a valid string"
            )
        
        try:
            # Step 1: Get tool definition
            tool_def = self.tool_registry.get_tool(tool_name)
            if not tool_def:
                return self._format_invalid_tool_response(
                    tool_call, 
                    f"Unknown tool '{tool_name}'. Available tools: {list(self.tool_registry.get_all_tools().keys())}"
                )
            
            # Step 2: Build service arguments
            service_args = self._build_service_arguments(
                agent_username, tool_def, parameters
            )
            
            # Step 3: Execute platform service
            db_result = self._execute_platform_service(tool_def.service, service_args)
            
            # Step 4: Format response
            formatted_response = tool_def.response_formatter(db_result)
            
            # Step 5: Record action for future context
            agent_tracker = self._get_agent_tracker(agent_username)
            agent_tracker.record_action(
                agent_username, tool_name, parameters, formatted_response
            )
            
            return formatted_response
            
        except Exception as e:
            # Handle errors gracefully
            error_response = {
                'success': False,
                'message': f'Tool execution failed: {str(e)}',
                'data': None,
                'tool': tool_name,
                'parameters': parameters
            }
            
            # Record failed action
            agent_tracker = self._get_agent_tracker(agent_username)
            agent_tracker.record_action(
                agent_username, tool_name, parameters, error_response
            )
            
            return error_response
    
    def _format_invalid_tool_response(self, tool_call: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """
        Format a response for invalid tool calls.
        
        Args:
            tool_call: The invalid tool call
            error_message: Description of what's wrong
            
        Returns:
            Formatted error response
        """
        return {
            'success': False,
            'message': f'Invalid tool call: {error_message}',
            'data': {
                'available_tools': [tool['name'] for tool in self.get_available_tools()],
                'tool_call_format': {
                    'tool': 'string (tool name)',
                    'parameters': 'dict (tool-specific parameters)'
                },
                'suggestion': 'Please check your tool call format and try again.'
            },
            'tool': tool_call.get('tool'),
            'parameters': tool_call.get('parameters', {})
        }
    
    def _build_service_arguments(self, agent_username: str, tool_def: ToolDefinition, 
                               tool_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build service arguments from tool parameters and context.
        
        Args:
            agent_username: The agent's username
            tool_def: The tool definition
            tool_parameters: Parameters provided by the agent
            
        Returns:
            Dictionary of service arguments
        """
        service_args = {}
        
        for service_arg, mapping_source in tool_def.arguments_mapping.items():
            # Check if mapping source is in tool parameters
            if mapping_source in tool_parameters:
                service_args[service_arg] = tool_parameters[mapping_source]
            
            # Check if mapping source is a context parameter
            elif mapping_source in tool_def.context_params:
                agent_tracker = self._get_agent_tracker(agent_username)
                context_value = agent_tracker.resolve_context_value(
                    agent_username, mapping_source, tool_parameters
                )
                if context_value is not None:
                    service_args[service_arg] = context_value
                else:
                    raise ValueError(f"Cannot resolve context parameter: {mapping_source}")
            
            # Direct mapping (same name)
            elif mapping_source == service_arg and mapping_source in tool_parameters:
                service_args[service_arg] = tool_parameters[mapping_source]
            
            else:
                raise ValueError(f"Cannot map service argument '{service_arg}' from source '{mapping_source}'")
        
        return service_args
    
    def _execute_platform_service(self, service_name: str, service_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a platform service with the given arguments.
        
        Args:
            service_name: Name of the platform service
            service_args: Arguments for the service
            
        Returns:
            Raw result from the platform service
        """
        service_func = self._service_cache.get(service_name)
        if service_func is None:
            raise ValueError(f"Platform service not available: {service_name}")
        
        # Get database session and execute service
        with self.db_manager.get_session() as session:
            try:
                # Add session to arguments
                full_args = {'session': session, **service_args}
                
                # Execute service
                result = service_func(**full_args)
                
                # Ensure result is in standard format
                if result is None:
                    return {'success': False, 'message': 'Service returned None', 'data': None}
                
                # If result doesn't have success key, wrap it
                if not isinstance(result, dict) or 'success' not in result:
                    return {'success': True, 'message': 'Service executed successfully', 'data': result}
                
                return result
                
            except Exception as e:
                return {
                    'success': False,
                    'message': f'Service execution failed: {str(e)}',
                    'data': None
                }
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of available tools in schema format.
        
        Returns:
            List of tool schemas suitable for LLM consumption
        """
        return self.tool_registry.get_tools_schema()
    
    def get_agent_context(self, agent_username: str) -> Dict[str, Any]:
        """
        Get current context for an agent.
        
        Args:
            agent_username: The agent's username
            
        Returns:
            Dictionary containing agent's current context
        """
        agent_tracker = self._get_agent_tracker(agent_username)
        return agent_tracker.get_agent_context(agent_username)
    
    def clear_agent_history(self, agent_username: str):
        """Clear action history for a specific agent."""
        if agent_username in self._agent_trackers:
            del self._agent_trackers[agent_username]
    
    def clear_all_agent_history(self):
        """Clear action history for all agents."""
        self._agent_trackers.clear()
    
    def register_custom_tool(self, tool_def: ToolDefinition):
        """Register a custom tool definition."""
        self.tool_registry.register_tool(tool_def)
        # Rebuild service cache to include any new services
        self._service_cache = self._build_service_cache()
    
    def register_custom_service(self, service_name: str, service_func: callable):
        """Register a custom platform service."""
        self._service_cache[service_name] = service_func
    
    def execute_tool_calls(self, agent_usernames: List[str], tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute multiple tool calls sequentially for an agent.
        
        Args:
            agent_username: The agent's username
            tool_calls: List of tool call dictionaries from the agent
            
        Returns:
            List of response dictionaries in the same order as tool_calls
        """
        results = []
        for (agent_username, tool_call) in zip(agent_usernames, tool_calls):
            result = self.execute_tool_call(agent_username, tool_call)
            results.append(result)
        return results

    

