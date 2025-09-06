"""
Example usage of the runtime layer components.

This demonstrates the complete workflow from agent tool calls to database operations.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agora.platform import DatabaseManager, initialize_database, services
from agora.runtime import AgentToolExecutor, ToolRegistry, ToolDefinition

def main():
    """Demonstrate the complete tool execution workflow."""
    
    # Initialize database
    print("🚀 Initializing Synthetic Agora Runtime...")
    db_manager = initialize_database("example_runtime.db")
    
    # Create the runtime executor
    executor = AgentToolExecutor(db_manager)
    
    print(f"✅ Runtime initialized with {len(executor.get_available_tools())} available tools")
    
    # Example 1: Create a user (using database service directly)
    print("\n📝 Example 1: Creating a user...")
    with db_manager.get_session() as session:
        result = services.create_user_account(
            session, 
            "alice", 
            "AI researcher exploring social dynamics"
        )
        print(f"Result: {result['message']}")
    
    # Create another user for testing
    with db_manager.get_session() as session:
        result = services.create_user_account(
            session, 
            "bob", 
            "Social media enthusiast"
        )
        print(f"Created user Bob: {result['message']}")
    
    # Example 2: Create a post
    print("\n📝 Example 2: Creating a post...")
    result = executor.execute_tool_call("alice", {
        "tool": "create_post",
        "parameters": {
            "title": "Hello World",
            "content": "This is my first post in the synthetic agora!"
        }
    })
    print(f"Result: {result['message']}")
    
    # Example 3: Follow a user
    print("\n👥 Example 3: Following a user...")
    result = executor.execute_tool_call("alice", {
        "tool": "follow_user",
        "parameters": {"username": "bob"}
    })
    print(f"Result: {result['message']}")
    
    # Example 4: Get feed
    print("\n📱 Example 4: Getting feed...")
    result = executor.execute_tool_call("alice", {
        "tool": "get_feed",
        "parameters": {"limit": 10}
    })
    print(f"Result: {result['message']}")
    if result['success']:
        print(f"Feed contains {len(result['data']['posts'])} posts")
    
    # Example 5: Like a post (this will use context resolution)
    print("\n❤️ Example 5: Liking a post...")
    result = executor.execute_tool_call("alice", {
        "tool": "like_post",
        "parameters": {"title": "Hello World"}
    })
    print(f"Result: {result['message']}")
    
    # Example 6: Show agent context
    print("\n📊 Example 6: Agent context...")
    context = executor.get_agent_context("alice")
    print(f"Agent Alice has performed {context['action_count']} actions")
    print(f"Recent posts: {[p['title'] for p in context['recent_posts']]}")
    
    # Example 7: Custom tool registration
    print("\n🔧 Example 7: Custom tool registration...")
    
    # Define a custom tool
    custom_tool = ToolDefinition(
        tool="get_user_stats",
        description="Get detailed statistics for a user",
        parameters={
            "username": {
                "type": "string",
                "description": "Username to get stats for"
            }
        },
        service="get_user_stats",
        arguments_mapping={
            "username": "username"
        },
        context_params=[],
        response_formatter="format_user_stats_response"
    )
    
    # Register the custom tool and its response formatter
    def format_user_stats_response(db_result):
        if not db_result.get('success'):
            return db_result
        return {
            'success': True,
            'message': 'User statistics retrieved',
            'data': {
                'action': 'get_user_stats',
                'stats': db_result.get('data')
            }
        }
    
    # Update the custom tool to include the formatter directly
    custom_tool.response_formatter = format_user_stats_response
    executor.register_custom_tool(custom_tool)
    
    print("✅ Custom tool registered")
    
    # Example 8: Use custom tool
    print("\n📈 Example 8: Using custom tool...")
    result = executor.execute_tool_calls(["alice"], [{
        "tool": "get_user_stats",
        "parameters": {"username": "alice"}
    }])[0]
    print(f"Result: {result['message']}")
    if result['success']:
        stats = result['data']['stats']
        print(f"  - Total posts: {stats.get('total_posts', 0)}")
        print(f"  - Total likes: {stats.get('total_likes_received', 0)}")
    
    # Example 9: Show all available tools
    print("\n🛠️ Example 9: Available tools...")
    tools = executor.get_available_tools()
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")
    
    # Example 10: Test invalid tool calls
    print("\n🚫 Example 10: Testing invalid tool calls...")
    
    # Invalid tool call - missing tool name
    result = executor.execute_tool_call("alice", {"parameters": {}})
    print(f"Invalid tool (missing name): {result['message']}")
    
    # Invalid tool call - missing parameters
    result = executor.execute_tool_call("alice", {"tool": "like_post"})
    print(f"Invalid tool (missing params): {result['message']}")
    
    # Invalid tool call - unknown tool
    result = executor.execute_tool_call("alice", {
        "tool": "nonexistent_tool",
        "parameters": {"test": "value"}
    })
    print(f"Invalid tool (unknown tool): {result['message']}")
    
    print("\n✨ Runtime demonstration completed!")
    
    # Cleanup
    db_manager.close()
    import os
    if os.path.exists("example_runtime.db"):
        os.remove("example_runtime.db")

if __name__ == "__main__":
    main()