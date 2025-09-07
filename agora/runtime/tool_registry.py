"""
Tool definition and registry for agent tools.

Defines the mapping between semantic agent tools and unified database services.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Callable


@dataclass
class ToolDefinition:
    """Defines how an agent tool maps to a database service."""
    
    tool: str  # Tool name, e.g., "create_post"
    description: str  # Tool description for agents
    parameters: Dict[str, Any]  # Parameters agents should provide
    service: str  # Database service name, e.g., "agent_create_post"
    arguments_mapping: Dict[str, str]  # Maps service args to tool params or context
    context_params: List[str]  # Parameters to infer from context
    response_formatter: Callable[[Dict[str, Any]], Dict[str, Any]]  # Response formatting function


class ToolRegistry:
    """Registry of all available agent tools and their mappings."""
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register the 9 core unified social media tools."""
        
        # 1. Create post tool
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
            description="Create a new post with title and content",
            parameters={
                "title": {
                    "type": "string",
                    "description": "Title of the post"
                },
                "content": {
                    "type": "string",
                    "description": "Content of the post"
                }
            },
            service="agent_create_post",
            arguments_mapping={
                "title": "title",
                "content": "content"
            },
            context_params=["agent_username"],
            response_formatter=format_create_post_response
        ))
        
        # 2. Create response tool (comments and replies)
        def format_create_response_response(db_result: Dict[str, Any]) -> Dict[str, Any]:
            """Format create_response response."""
            if not db_result.get('success'):
                return db_result
            return {
                'success': True,
                'message': db_result.get('message', 'Response created successfully'),
                'data': {
                    'action': 'create_response',
                    'response': db_result.get('data')
                }
            }
        
        self.register_tool(ToolDefinition(
            tool="create_response",
            description="Create a comment or reply on a post",
            parameters={
                "content_type": {
                    "type": "string",
                    "description": "Type of response: 'comment' or 'reply'",
                    "enum": ["comment", "reply"]
                },
                "post_id": {
                    "type": "integer",
                    "description": "ID of the post to respond to"
                },
                "content": {
                    "type": "string",
                    "description": "Content of the response"
                }
            },
            service="agent_create_response",
            arguments_mapping={
                "content_type": "content_type",
                "post_id": "post_id",
                "content": "content"
            },
            context_params=["agent_username"],
            response_formatter=format_create_response_response
        ))
        
        # 3. View post tool
        def format_view_post_response(db_result: Dict[str, Any]) -> Dict[str, Any]:
            """Format view_post response."""
            if not db_result.get('success'):
                return db_result
            return {
                'success': True,
                'message': db_result.get('message', 'Post viewed successfully'),
                'data': {
                    'action': 'view_post',
                    'post_data': db_result.get('data')
                }
            }
        
        self.register_tool(ToolDefinition(
            tool="view_post",
            description="View post details, reactions, or comments",
            parameters={
                "view_type": {
                    "type": "string",
                    "description": "What to view: 'overview', 'reactions', or 'comments'",
                    "enum": ["overview", "reactions", "comments"]
                },
                "post_id": {
                    "type": "integer",
                    "description": "ID of the post to view"
                }
            },
            service="agent_view_post",
            arguments_mapping={
                "view_type": "view_type",
                "post_id": "post_id"
            },
            context_params=["agent_username"],
            response_formatter=format_view_post_response
        ))
        
        # 4. React to post tool
        def format_react_to_post_response(db_result: Dict[str, Any]) -> Dict[str, Any]:
            """Format react_to_post response."""
            if not db_result.get('success'):
                return db_result
            return {
                'success': True,
                'message': db_result.get('message', 'Post reaction completed'),
                'data': {
                    'action': 'react_to_post',
                    'reaction_data': db_result.get('data')
                }
            }
        
        self.register_tool(ToolDefinition(
            tool="react_to_post",
            description="Like, unlike, or share a post",
            parameters={
                "reaction_type": {
                    "type": "string",
                    "description": "Type of reaction: 'like', 'unlike', or 'share'",
                    "enum": ["like", "unlike", "share"]
                },
                "post_id": {
                    "type": "integer",
                    "description": "ID of the post to react to"
                },
                "comment": {
                    "type": "string",
                    "description": "Optional comment when sharing",
                    "required": False
                }
            },
            service="agent_react_to_post",
            arguments_mapping={
                "reaction_type": "reaction_type",
                "post_id": "post_id",
                "comment": "comment"
            },
            context_params=["agent_username"],
            response_formatter=format_react_to_post_response
        ))
        
        # 5. React to response tool
        def format_react_to_response_response(db_result: Dict[str, Any]) -> Dict[str, Any]:
            """Format react_to_response response."""
            if not db_result.get('success'):
                return db_result
            return {
                'success': True,
                'message': db_result.get('message', 'Response reaction completed'),
                'data': {
                    'action': 'react_to_response',
                    'reaction_data': db_result.get('data')
                }
            }
        
        self.register_tool(ToolDefinition(
            tool="react_to_response",
            description="Like or unlike a comment/reply",
            parameters={
                "resolution_type": {
                    "type": "string",
                    "description": "Type of resolution: 'like' or 'unlike'",
                    "enum": ["like", "unlike"]
                },
                "post_id": {
                    "type": "integer",
                    "description": "ID of the response to react to"
                },
                "reaction_type": {
                    "type": "string",
                    "description": "Always 'like' for response reactions"
                }
            },
            service="agent_react_to_response",
            arguments_mapping={
                "resolution_type": "resolution_type",
                "post_id": "post_id",
                "reaction_type": "reaction_type"
            },
            context_params=["agent_username"],
            response_formatter=format_react_to_response_response
        ))
        
        # 6. Connect with user tool
        def format_connect_with_user_response(db_result: Dict[str, Any]) -> Dict[str, Any]:
            """Format connect_with_user response."""
            if not db_result.get('success'):
                return db_result
            return {
                'success': True,
                'message': db_result.get('message', 'User connection completed'),
                'data': {
                    'action': 'connect_with_user',
                    'connection_data': db_result.get('data')
                }
            }
        
        self.register_tool(ToolDefinition(
            tool="connect_with_user",
            description="Follow, unfollow, or get user profile/relationship/posts",
            parameters={
                "action_type": {
                    "type": "string",
                    "description": "Action: 'follow', 'unfollow', 'get_profile', 'get_relationship', 'get_posts'",
                    "enum": ["follow", "unfollow", "get_profile", "get_relationship", "get_posts"]
                },
                "target_username": {
                    "type": "string",
                    "description": "Username of the target user"
                }
            },
            service="agent_connect_with_user",
            arguments_mapping={
                "action_type": "action_type",
                "target_username": "target_username"
            },
            context_params=["agent_username"],
            response_formatter=format_connect_with_user_response
        ))
        
        # 7. Manage community tool
        def format_manage_community_response(db_result: Dict[str, Any]) -> Dict[str, Any]:
            """Format manage_community response."""
            if not db_result.get('success'):
                return db_result
            return {
                'success': True,
                'message': db_result.get('message', 'Community management completed'),
                'data': {
                    'action': 'manage_community',
                    'community_data': db_result.get('data')
                }
            }
        
        self.register_tool(ToolDefinition(
            tool="manage_community",
            description="Create, join, leave, or get community information",
            parameters={
                "action_type": {
                    "type": "string",
                    "description": "Action: 'create', 'join', 'leave', 'get_info', 'get_members'",
                    "enum": ["create", "join", "leave", "get_info", "get_members"]
                },
                "community_name": {
                    "type": "string",
                    "description": "Name of the community"
                },
                "description": {
                    "type": "string",
                    "description": "Description for community creation",
                    "required": False
                }
            },
            service="agent_manage_community",
            arguments_mapping={
                "action_type": "action_type",
                "community_name": "community_name",
                "description": "description"
            },
            context_params=["agent_username"],
            response_formatter=format_manage_community_response
        ))
        
        # 8. Get discovery tool
        def format_get_discovery_response(db_result: Dict[str, Any]) -> Dict[str, Any]:
            """Format get_discovery response."""
            if not db_result.get('success'):
                return db_result
            return {
                'success': True,
                'message': db_result.get('message', 'Discovery content retrieved'),
                'data': {
                    'action': 'get_discovery',
                    'discovery_data': db_result.get('data')
                }
            }
        
        self.register_tool(ToolDefinition(
            tool="get_discovery",
            description="Get personalized feed or trending content",
            parameters={
                "discovery_type": {
                    "type": "string",
                    "description": "Type of discovery: 'feed' or 'trending'",
                    "enum": ["feed", "trending"]
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of items to return",
                    "default": 20,
                    "required": False
                }
            },
            service="agent_get_discovery",
            arguments_mapping={
                "discovery_type": "discovery_type",
                "limit": "limit"
            },
            context_params=["agent_username"],
            response_formatter=format_get_discovery_response
        ))
        
        # 9. Search tool
        def format_search_response(db_result: Dict[str, Any]) -> Dict[str, Any]:
            """Format search response."""
            if not db_result.get('success'):
                return db_result
            return {
                'success': True,
                'message': db_result.get('message', 'Search completed'),
                'data': {
                    'action': 'search',
                    'search_results': db_result.get('data')
                }
            }
        
        self.register_tool(ToolDefinition(
            tool="search",
            description="Search across posts, users, and communities",
            parameters={
                "query": {
                    "type": "string",
                    "description": "Search query (case-insensitive)"
                },
                "search_type": {
                    "type": "string",
                    "description": "What to search: 'all', 'posts', 'users', or 'communities'",
                    "default": "all",
                    "enum": ["all", "posts", "users", "communities"],
                    "required": False
                }
            },
            service="agent_search",
            arguments_mapping={
                "query": "query",
                "search_type": "search_type"
            },
            context_params=["agent_username"],
            response_formatter=format_search_response
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
    
    