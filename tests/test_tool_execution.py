#!/usr/bin/env python3
"""
Integration test for the complete tool execution pipeline.

Tests that tools can actually execute using the refactored tool registry.
"""

import sys
from pathlib import Path

# Add the agora directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agora.platform.connection import initialize_database
from agora.runtime.tool_registry import ToolRegistry
from agora.runtime.tool_executor import AgentToolExecutor
from agora.platform import services


def test_tool_execution():
    """Test that tools can actually execute end-to-end."""
    print("🚀 Testing Tool Execution Pipeline")
    print("=" * 50)
    
    # Initialize database
    test_db_path = "test_tool_execution.db"
    db = initialize_database(test_db_path)
    
    try:
        # Initialize tool executor
        registry = ToolRegistry()
        executor = AgentToolExecutor(db, registry)
        
        # Test 1: Create a user first
        print("\n1. Creating test user...")
        with db.get_session() as session:
            user_result = services.create_user_account(session, "test_agent", "Test agent for tool execution")
            print(f"   User creation: {'✅' if user_result['success'] else '❌'}")
            if not user_result['success']:
                print(f"   Error: {user_result['message']}")
                return False
        
        # Test 2: Create a post using tool executor
        print("\n2. Testing create_post tool...")
        tool_call = {
            "tool": "create_post",
            "parameters": {
                "title": "Test Post from Tool",
                "content": "This is a test post created through the tool executor."
            }
        }
        
        result = executor.execute_tool_call("test_agent", tool_call)
        print(f"   Create post: {'✅' if result['success'] else '❌'}")
        if result['success']:
            print(f"   Response data: {result['data']}")
            # For now, we'll get the post ID from the database
            with db.get_session() as session:
                from agora.platform.operations import get_post_by_title
                post = get_post_by_title(session, "Test Post from Tool")
                if post:
                    post_id = post.id
                    print(f"   Post ID: {post_id}")
                else:
                    print("   Could not find post in database")
                    return False
        else:
            print(f"   Error: {result['message']}")
            return False
        
        # Test 3: View the post
        print("\n3. Testing view_post tool...")
        tool_call = {
            "tool": "view_post",
            "parameters": {
                "view_type": "overview",
                "post_id": post_id
            }
        }
        
        result = executor.execute_tool_call("test_agent", tool_call)
        print(f"   View post: {'✅' if result['success'] else '❌'}")
        if result['success']:
            post_data = result['data']['post_data']
            print(f"   Post title: {post_data['title']}")
        else:
            print(f"   Error: {result['message']}")
            return False
        
        # Test 4: React to the post
        print("\n4. Testing react_to_post tool...")
        tool_call = {
            "tool": "react_to_post",
            "parameters": {
                "reaction_type": "like",
                "post_id": post_id
            }
        }
        
        result = executor.execute_tool_call("test_agent", tool_call)
        print(f"   Like post: {'✅' if result['success'] else '❌'}")
        if not result['success']:
            print(f"   Error: {result['message']}")
            return False
        
        # Test 5: Create a comment
        print("\n5. Testing create_response tool...")
        tool_call = {
            "tool": "create_response",
            "parameters": {
                "content_type": "comment",
                "post_id": post_id,
                "content": "Great post! This is a comment."
            }
        }
        
        result = executor.execute_tool_call("test_agent", tool_call)
        print(f"   Create comment: {'✅' if result['success'] else '❌'}")
        if result['success']:
            print(f"   Response data: {result['data']}")
            # Get the most recent comment for this post
            with db.get_session() as session:
                from agora.platform.operations import get_comments_for_post
                comments = get_comments_for_post(session, post_id)
                if comments:
                    comment_id = comments[0].id  # Most recent comment
                    print(f"   Comment ID: {comment_id}")
                else:
                    print("   Could not find comment in database")
                    return False
        else:
            print(f"   Error: {result['message']}")
            return False
        
        # Test 6: Get discovery feed
        print("\n6. Testing get_discovery tool...")
        tool_call = {
            "tool": "get_discovery",
            "parameters": {
                "discovery_type": "feed",
                "limit": 5
            }
        }
        
        result = executor.execute_tool_call("test_agent", tool_call)
        print(f"   Get feed: {'✅' if result['success'] else '❌'}")
        if result['success']:
            feed_items = result['data']['discovery_data']['feed_items']
            print(f"   Feed items: {len(feed_items)}")
        else:
            print(f"   Error: {result['message']}")
            return False
        
        # Test 7: Search
        print("\n7. Testing search tool...")
        tool_call = {
            "tool": "search",
            "parameters": {
                "query": "Test Post",
                "search_type": "posts"
            }
        }
        
        result = executor.execute_tool_call("test_agent", tool_call)
        print(f"   Search: {'✅' if result['success'] else '❌'}")
        if result['success']:
            search_results = result['data']['search_results']
            print(f"   Search results: {len(search_results)}")
        else:
            print(f"   Error: {result['message']}")
            return False
        
        # Test 8: Create a community
        print("\n8. Testing manage_community tool...")
        tool_call = {
            "tool": "manage_community",
            "parameters": {
                "action_type": "create",
                "community_name": "Test Community",
                "description": "A test community for tool execution"
            }
        }
        
        result = executor.execute_tool_call("test_agent", tool_call)
        print(f"   Create community: {'✅' if result['success'] else '❌'}")
        if result['success']:
            print(f"   Response data: {result['data']}")
            community_data = result['data']['community_data']
            print(f"   Community: {community_data.get('community_name', 'Name not found')}")
        else:
            print(f"   Error: {result['message']}")
            return False
        
        print("\n🎉 All tool execution tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        db.close()
        Path(test_db_path).unlink(missing_ok=True)


if __name__ == "__main__":
    success = test_tool_execution()
    sys.exit(0 if success else 1)