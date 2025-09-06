"""
Tool definition and registry for agent tools.

Defines the mapping between semantic agent tools and database services.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Callable


@dataclass
class ToolDefinition:
    """Defines how an agent tool maps to a database service."""
    
    tool: str  # Tool name, e.g., "create_post"
    description: str  # Tool description for agents
    parameters: Dict[str, Any]  # Parameters agents should provide
    service: str  # Database service name, e.g., "create_user_post"
    arguments_mapping: Dict[str, str]  # Maps service args to tool params or context
    context_params: List[str]  # Parameters to infer from context
    response_formatter: Callable[[Dict[str, Any]], Dict[str, Any]]  # Response formatting function


class ToolRegistry:
    """Registry of all available agent tools and their mappings."""
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register the default set of social media tools."""
        
        # Like post tool
        def format_like_response(db_result: Dict[str, Any]) -> Dict[str, Any]:
            """Format like_post response."""
            if not db_result.get('success'):
                return db_result
            return {
                'success': True,
                'message': db_result.get('message', 'Post liked successfully'),
                'data': {
                    'action': 'like_post',
                    'reaction_counts': db_result.get('data', {}).get('reaction_counts', {})
                }
            }
        
        self.register_tool(ToolDefinition(
            tool="like_post",
            description="Like a post by its title",
            parameters={
                "title": {
                    "type": "string",
                    "description": "Title of the post to like"
                }
            },
            service="like_post",
            arguments_mapping={
                "username": "agent_username",
                "post_id": "target_post_id"
            },
            context_params=["agent_username", "target_post_id"],
            response_formatter=format_like_response
        ))
        
        # Create post tool
        def format_create_post_response(db_result: Dict[str, Any]) -> Dict[str, Any]:
            """Format create_post response."""
            if not db_result.get('success'):
                return db_result
            return {
                'success': True,
                'message': db_result.get('message', 'Post created successfully'),
                'data': {
                    'action': 'create_post',
                    'post': db_result.get('data')
                }
            }
        
        self.register_tool(ToolDefinition(
            tool="create_post",
            description="Create a new post",
            parameters={
                "content": {
                    "type": "string", 
                    "description": "Content of the post"
                },
                "title": {
                    "type": "string",
                    "description": "Title for the post",
                    "required": False
                }
            },
            service="create_user_post",
            arguments_mapping={
                "username": "agent_username",
                "content": "content",
                "title": "title"
            },
            context_params=["agent_username"],
            response_formatter=format_create_post_response
        ))
        
        # Follow user tool
        def format_follow_response(db_result: Dict[str, Any]) -> Dict[str, Any]:
            """Format follow_user response."""
            if not db_result.get('success'):
                return db_result
            return {
                'success': True,
                'message': db_result.get('message', 'User followed successfully'),
                'data': {
                    'action': 'follow_user',
                    'following_count': db_result.get('data', {}).get('following_count', 0)
                }
            }
        
        self.register_tool(ToolDefinition(
            tool="follow_user",
            description="Follow another user",
            parameters={
                "username": {
                    "type": "string",
                    "description": "Username of the user to follow"
                }
            },
            service="follow_user",
            arguments_mapping={
                "follower_username": "agent_username",
                "followed_username": "username"
            },
            context_params=["agent_username"],
            response_formatter=format_follow_response
        ))
        
        # Get feed tool
        def format_feed_response(db_result: Dict[str, Any]) -> Dict[str, Any]:
            """Format get_feed response."""
            if not db_result.get('success'):
                return db_result
            return {
                'success': True,
                'message': 'Feed retrieved successfully',
                'data': {
                    'action': 'get_feed',
                    'posts': [item.get('post', {}) for item in db_result.get('data', [])],
                    'scores': [item.get('relevance_score', 0) for item in db_result.get('data', [])]
                }
            }
        
        self.register_tool(ToolDefinition(
            tool="get_feed",
            description="Get your personalized feed",
            parameters={
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of posts to return",
                    "default": 20,
                    "required": False
                }
            },
            service="get_user_feed",
            arguments_mapping={
                "username": "agent_username",
                "limit": "limit"
            },
            context_params=["agent_username"],
            response_formatter=format_feed_response
        ))
        
        # Get post details tool
        def format_post_details_response(db_result: Dict[str, Any]) -> Dict[str, Any]:
            """Format get_post_details response."""
            if not db_result.get('success'):
                return db_result
            return {
                'success': True,
                'message': 'Post details retrieved successfully',
                'data': {
                    'action': 'get_post_details',
                    'post': db_result.get('data')
                }
            }
        
        self.register_tool(ToolDefinition(
            tool="get_post_details",
            description="Get detailed information about a post",
            parameters={
                "title": {
                    "type": "string",
                    "description": "Title of the post to get details for"
                }
            },
            service="get_post_details",
            arguments_mapping={
                "post_id": "target_post_id"
            },
            context_params=["target_post_id"],
            response_formatter=format_post_details_response
        ))
        
        # Create comment tool
        def format_create_comment_response(db_result: Dict[str, Any]) -> Dict[str, Any]:
            """Format create_comment response."""
            if not db_result.get('success'):
                return db_result
            return {
                'success': True,
                'message': db_result.get('message', 'Comment created successfully'),
                'data': {
                    'action': 'create_comment',
                    'comment': db_result.get('data')
                }
            }
        
        self.register_tool(ToolDefinition(
            tool="create_comment",
            description="Create a comment on a post",
            parameters={
                "title": {
                    "type": "string",
                    "description": "Title of the post to comment on"
                },
                "content": {
                    "type": "string",
                    "description": "Content of the comment"
                }
            },
            service="create_comment",
            arguments_mapping={
                "username": "agent_username",
                "post_id": "target_post_id",
                "content": "content"
            },
            context_params=["agent_username", "target_post_id"],
            response_formatter=format_create_comment_response
        ))
    
    
    def register_tool(self, tool_def: ToolDefinition):
        """Register a new tool definition."""
        self._tools[tool_def.tool] = tool_def
    
    def get_tool(self, tool_name: str) -> Optional[ToolDefinition]:
        """Get a tool definition by name."""
        return self._tools.get(tool_name)
    
    def get_all_tools(self) -> Dict[str, ToolDefinition]:
        """Get all registered tools."""
        return self._tools.copy()
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Get all tools in a schema format suitable for LLM consumption."""
        schema = []
        for tool_def in self._tools.values():
            tool_schema = {
                "name": tool_def.tool,
                "description": tool_def.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
            
            # Convert parameters to JSON schema format
            for param_name, param_info in tool_def.parameters.items():
                tool_schema["parameters"]["properties"][param_name] = {
                    "type": param_info.get("type", "string"),
                    "description": param_info.get("description", "")
                }
                
                if param_info.get("required", True):
                    tool_schema["parameters"]["required"].append(param_name)
            
            schema.append(tool_schema)
        
        return schema
    
    def format_response(self, tool_name: str, db_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format a database service response using the appropriate formatter."""
        tool_def = self.get_tool(tool_name)
        if not tool_def:
            return db_result
        
        return tool_def.response_formatter(db_result)
    
    