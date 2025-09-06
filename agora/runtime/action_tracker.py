"""
Action tracking for agent context resolution.

Tracks agent actions to resolve semantic identifiers to database IDs.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class ActionRecord:
    """Record of an agent action for context tracking."""
    
    agent_username: str
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ActionTracker:
    """Tracks agent actions to resolve semantic identifiers to database IDs."""
    
    def __init__(self):
        self._actions: List[ActionRecord] = []
    
    def record_action(self, agent_username: str, tool_name: str, 
                     parameters: Dict[str, Any], result: Optional[Dict[str, Any]] = None):
        """Record an agent action for future reference."""
        action = ActionRecord(agent_username, tool_name, parameters, result)
        self._actions.append(action)
    
    def resolve_context_value(self, agent_username: str, context_param: str, 
                            tool_parameters: Dict[str, Any]) -> Any:
        """
        Resolve a context parameter value for an agent.
        
        Args:
            agent_username: The agent's username
            context_param: The context parameter to resolve (e.g., "target_post_id")
            tool_parameters: The current tool's parameters
            
        Returns:
            The resolved value or None if not found
        """
        if context_param == "agent_username":
            return agent_username
        
        elif context_param == "target_post_id":
            # Try to resolve post_id from tool parameters first
            if "title" in tool_parameters:
                return self.resolve_post_id_by_title(agent_username, tool_parameters["title"])
        
        elif context_param == "target_user_id":
            # Try to resolve user_id from tool parameters
            if "username" in tool_parameters:
                return self.resolve_user_id_by_username(tool_parameters["username"])
        
        return None
    
    def resolve_post_id_by_title(self, agent_username: str, title: str) -> Optional[int]:
        """
        Find the most recent post with given title that the agent interacted with.
        
        Args:
            agent_username: The agent's username
            title: The post title to search for
            
        Returns:
            Post ID if found, None otherwise
        """
        # Look for posts in agent's action history, most recent first
        for action in reversed(self._actions):
            if action.agent_username != agent_username:
                continue
            
            # Check if this action returned post information
            if action.result and action.result.get('success'):
                data = action.result.get('data', {})
                
                # Check if data is a post object
                if isinstance(data, dict) and data.get('title') == title:
                    return data.get('id')
                
                # Check if data contains a post (e.g., in create_post response)
                if isinstance(data, dict) and 'post' in data:
                    post = data['post']
                    if isinstance(post, dict) and post.get('title') == title:
                        return post.get('id')
                
                # Check if data is a list of posts (e.g., feed response)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and 'post' in item:
                            post = item['post']
                            if isinstance(post, dict) and post.get('title') == title:
                                return post.get('id')
            
            # Check if this was a post creation action
            if action.tool_name in ['create_post', 'create_comment']:
                if action.parameters.get('title') == title:
                    # For created posts, we need to find the ID from result
                    if action.result and action.result.get('success'):
                        result_data = action.result.get('data', {})
                        if isinstance(result_data, dict):
                            # Check for post object in result
                            if 'post' in result_data:
                                return result_data['post'].get('id')
                            # Check if result data itself is the post
                            if result_data.get('title') == title:
                                return result_data.get('id')
        
        return None
    
    def resolve_user_id_by_username(self, username: str) -> Optional[int]:
        """
        Find user ID from action history.
        
        Note: In most cases, we'll query the database directly for user IDs.
        This method is here for consistency and potential future use cases.
        
        Args:
            username: The username to resolve
            
        Returns:
            User ID if found in context, None otherwise
        """
        # Look for user interactions in action history
        for action in reversed(self._actions):
            if action.result and action.result.get('success'):
                data = action.result.get('data', {})
                
                # Check various places where user information might appear
                if isinstance(data, dict):
                    # Direct user info
                    if data.get('username') == username and 'id' in data:
                        return data['id']
                    
                    # Post author info
                    if data.get('author_username') == username:
                        # We'd need to query the database for the author's ID
                        # For now, return None to trigger database lookup
                        return None
                    
                    # User profile info
                    if data.get('username') == username and 'id' in data:
                        return data['id']
        
        return None
    
    def get_agent_context(self, agent_username: str) -> Dict[str, Any]:
        """
        Get recent context for an agent.
        
        Args:
            agent_username: The agent's username
            
        Returns:
            Dictionary containing agent's recent context
        """
        agent_actions = [a for a in self._actions if a.agent_username == agent_username]
        recent_actions = agent_actions[-10:]  # Last 10 actions
        
        # Extract recent posts from actions
        recent_posts = []
        for action in recent_actions:
            if action.result and action.result.get('success'):
                data = action.result.get('data', {})
                
                # Handle different response formats
                if isinstance(data, dict):
                    # Direct post object
                    if 'title' in data and 'content' in data:
                        recent_posts.append(data)
                    
                    # Post wrapped in response
                    elif 'post' in data:
                        recent_posts.append(data['post'])
                    
                    # List of posts (feed response)
                    elif 'posts' in data and isinstance(data['posts'], list):
                        recent_posts.extend(data['posts'])
                
                # Handle list data (feed items)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and 'post' in item:
                            recent_posts.append(item['post'])
        
        # Remove duplicates and limit to most recent
        seen_titles = set()
        unique_posts = []
        for post in reversed(recent_posts):
            if post.get('title') not in seen_titles:
                unique_posts.append(post)
                seen_titles.add(post.get('title'))
                if len(unique_posts) >= 5:  # Keep only 5 most recent unique posts
                    break
        
        return {
            'recent_posts': list(reversed(unique_posts)),  # Put back in chronological order
            'action_count': len(agent_actions),
            'recent_actions': [
                {
                    'tool': action.tool_name,
                    'timestamp': action.timestamp.isoformat(),
                    'success': action.result.get('success', False) if action.result else False
                }
                for action in recent_actions[-5:]  # Last 5 actions
            ]
        }
    
    def clear_agent_history(self, agent_username: str):
        """Clear action history for a specific agent."""
        self._actions = [a for a in self._actions if a.agent_username != agent_username]
    
    def clear_all_history(self):
        """Clear all action history."""
        self._actions.clear()