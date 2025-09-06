"""
Basic tests for the runtime layer components.
"""

def test_tool_executor_initialization(tool_executor):
    """Test that the tool executor initializes correctly."""
    assert tool_executor is not None
    tools = tool_executor.get_available_tools()
    assert len(tools) > 0
    assert any(tool['name'] == 'like_post' for tool in tools)


def test_create_post_tool(tool_executor, sample_users):
    """Test the create_post tool."""
    result = tool_executor.execute_tool_call("alice", {
        "tool": "create_post",
        "parameters": {
            "title": "Test Post",
            "content": "This is a test post"
        }
    })
    
    assert result['success'] is True
    assert result['data']['post']['title'] == "Test Post"
    assert result['data']['post']['author_username'] == "alice"


def test_like_post_tool(tool_executor, sample_users):
    """Test the like_post tool with context resolution."""
    # First create a post
    result = tool_executor.execute_tool_call("alice", {
        "tool": "create_post",
        "parameters": {
            "title": "Likeable Post",
            "content": "This post should be liked"
        }
    })
    
    # Then like it (same user who created it)
    result = tool_executor.execute_tool_call("alice", {
        "tool": "like_post",
        "parameters": {"title": "Likeable Post"}
    })
    
    assert result['success'] is True
    assert "liked post" in result['message']


def test_follow_user_tool(tool_executor, sample_users):
    """Test the follow_user tool."""
    result = tool_executor.execute_tool_call("alice", {
        "tool": "follow_user",
        "parameters": {"username": "bob"}
    })
    
    assert result['success'] is True
    assert "following" in result['message']


def test_invalid_tool_calls(tool_executor):
    """Test that invalid tool calls are handled gracefully."""
    # Missing tool name
    result = tool_executor.execute_tool_call("alice", {"parameters": {}})
    assert result['success'] is False
    assert "tool" in result['message'].lower()
    
    # Missing parameters
    result = tool_executor.execute_tool_call("alice", {"tool": "like_post"})
    assert result['success'] is False
    assert "parameters" in result['message'].lower()
    
    # Unknown tool
    result = tool_executor.execute_tool_call("alice", {
        "tool": "nonexistent_tool",
        "parameters": {"test": "value"}
    })
    assert result['success'] is False
    assert "unknown" in result['message'].lower()


def test_agent_context_tracking(tool_executor, sample_users):
    """Test that agent actions are properly tracked."""
    # Perform some actions
    tool_executor.execute_tool_call("alice", {
        "tool": "create_post",
        "parameters": {"title": "Context Test", "content": "Testing context"}
    })
    
    tool_executor.execute_tool_call("alice", {
        "tool": "follow_user",
        "parameters": {"username": "bob"}
    })
    
    # Check context
    context = tool_executor.get_agent_context("alice")
    assert context['action_count'] == 2
    assert len(context['recent_posts']) == 1
    assert context['recent_posts'][0]['title'] == "Context Test"