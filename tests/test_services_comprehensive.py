#!/usr/bin/env python3
"""
Comprehensive test script for all unified services in @agora/platform/services.py

Tests all UNIFIED CONTENT SERVICES, UNIFIED DISCOVERY SERVICES, and UNIFIED SOCIAL SERVICES
"""

import sys
from pathlib import Path

# Add the agora directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agora.platform.services import (
    # USER SERVICES
    create_user_account,
    
    # UNIFIED CONTENT SERVICES
    agent_create_post,
    agent_create_response,
    agent_view_post,
    agent_react_to_post,
    agent_react_to_response,
    
    # UNIFIED DISCOVERY SERVICES  
    agent_get_discovery,
    agent_search,
    
    # UNIFIED SOCIAL SERVICES
    agent_connect_with_user,
    agent_manage_community,
)

from agora.platform.connection import initialize_database

def print_test_header(test_name):
    """Print test header with separator"""
    print(f"\n{'='*60}")
    print(f"TESTING: {test_name}")
    print(f"{'='*60}")

def print_result(test_name, result):
    """Print test result with success/failure indication and returned data"""
    status = "✅ PASS" if result["success"] else "❌ FAIL"
    print(f"  {status} | {test_name}")
    if not result["success"]:
        print(f"         Error: {result['message']}")
    else:
        print(f"         Message: {result['message']}")
        if result.get("data"):
            print(f"         Data: {result['data']}")

def test_user_services(session):
    """Test all USER SERVICES"""
    print_test_header("USER SERVICES")
    
    # Test user creation
    print("\n1. Creating test users...")
    users_to_create = [
        ("alice", "Alice Smith - Software Developer"),
        ("bob", "Bob Johnson - Data Scientist"),
        ("charlie", "Charlie Brown - Philosopher"),
        ("diana", "Diana Prince - Journalist")
    ]
    
    created_users = []
    for username, bio in users_to_create:
        result = create_user_account(session, username, bio)
        print_result(f"create_user_account({username})", result)
        if result["success"]:
            created_users.append(username)
    
    # Test user profiles
    print("\n2. Testing user profiles...")
    for username in created_users:
        for target_username in created_users:
            result = agent_connect_with_user(session, username, "get_profile", target_username)
            print_result(f"agent_connect_with_user({username}, get_profile, {target_username})", result)
    
    # Test user relationships
    print("\n3. Testing user relationships...")
    result = agent_connect_with_user(session, "alice", "get_relationship", "bob")
    print_result("agent_connect_with_user(alice, get_relationship, bob)", result)
    
    # Test user posts (should be empty initially)
    print("\n4. Testing user posts (initially empty)...")
    for username in created_users:
        result = agent_connect_with_user(session, username, "get_posts", username)
        print_result(f"agent_connect_with_user({username}, get_posts, {username})", result)
    
    return created_users

def test_content_services(session, _users):
    """Test all CONTENT SERVICES"""
    print_test_header("CONTENT SERVICES")
    
    # Create some posts
    print("\n1. Creating posts...")
    posts_data = [
        ("alice", "Introduction to Machine Learning", "Machine learning is a fascinating field that combines statistics, computer science, and domain expertise."),
        ("bob", "Data Visualization Tips", "Effective data visualization is crucial for communicating insights clearly and concisely."),
        ("charlie", "The Meaning of Life", "What is the meaning of life? This question has puzzled philosophers for centuries."),
        ("diana", "Breaking News: Tech Conference", "Major tech conference announced for next month. Industry leaders expected to attend.")
    ]
    
    created_posts = []
    for username, title, content in posts_data:
        result = agent_create_post(session, username, title, content)
        print_result(f"agent_create_post({username}, {title[:20]}...)", result)
        if result["success"]:
            created_posts.append((username, title, result["data"]))
    
    # Create comments and replies
    print("\n2. Creating comments and replies...")
    if len(created_posts) >= 2:
        # Comment on first post (post_id = 1)
        result = agent_create_response(session, "bob", "comment", 1, "Great insights! I especially liked your point about domain expertise.")
        print_result("agent_create_response(bob, comment, 1)", result)
        
        # Reply to comment (comment should get post_id = 5, the next available ID)
        if result["success"]:
            result2 = agent_create_response(session, "alice", "reply", 5, "Thanks Bob! I'm glad you found it useful.")
            print_result("agent_create_response(alice, reply, 5)", result2)
    
    # Test post viewing (overview, reactions, comments)
    print("\n3. Testing post viewing...")
    for i, (username, title, _data) in enumerate(created_posts[:2]):
        post_id = i + 1
        # Test overview
        result = agent_view_post(session, "alice", "overview", post_id)
        print_result(f"agent_view_post(alice, overview, {post_id})", result)
        
        # Test reactions
        result2 = agent_view_post(session, "alice", "reactions", post_id)
        print_result(f"agent_view_post(alice, reactions, {post_id})", result2)
        
        # Test comments
        result3 = agent_view_post(session, "alice", "comments", post_id)
        print_result(f"agent_view_post(alice, comments, {post_id})", result3)
    
    # Test reactions
    print("\n4. Testing reactions...")
    if len(created_posts) >= 2:
        # Like posts
        result1 = agent_react_to_post(session, "bob", "like", 1)
        print_result("agent_react_to_post(bob, like, 1)", result1)
        
        result2 = agent_react_to_post(session, "charlie", "like", 1)
        print_result("agent_react_to_post(charlie, like, 1)", result2)
        
        # Like comment (comment has post_id = 5)
        result3 = agent_react_to_response(session, "alice", "like", 5)
        print_result("agent_react_to_response(alice, like, 5)", result3)
        
        # Unlike post
        if result1["success"]:
            result4 = agent_react_to_post(session, "bob", "unlike", 1)
            print_result("agent_react_to_post(bob, unlike, 1)", result4)
    
    # Test sharing
    print("\n5. Testing post sharing...")
    if len(created_posts) >= 2:
        result = agent_react_to_post(session, "diana", "share", 1, "This is really interesting! Check it out.")
        print_result("agent_react_to_post(diana, share, 1)", result)
    
    return created_posts

def test_algorithm_services(session, _users):
    """Test ALGORITHM SERVICES"""
    print_test_header("ALGORITHM SERVICES")
    
    # Test user feeds
    print("\n1. Testing user feeds...")
    for username in _users[:2]:
        result = agent_get_discovery(session, username, "feed")
        if result["success"]:
            feed_items = result["data"]["feed_items"]
            print(f"  📊 | agent_get_discovery({username}, feed) -> {len(feed_items)} items")
        else:
            print(f"  ❌ | agent_get_discovery({username}, feed) failed: {result['message']}")
    
    # Test trending posts
    print("\n2. Testing trending posts...")
    result = agent_get_discovery(session, "alice", "trending", limit=5)
    if result["success"]:
        trending_posts = result["data"]["trending_posts"]
        print(f"  📊 | agent_get_discovery(alice, trending) -> {len(trending_posts)} items")
        for i, post in enumerate(trending_posts):
            print(f"      {i+1}. {post['title']} by @{post['author_username']} ({post['like_count']} likes)")
    else:
        print(f"  ❌ | agent_get_discovery(alice, trending) failed: {result['message']}")

def test_search_services(session, users):
    """Test SEARCH SERVICES"""
    print_test_header("SEARCH SERVICES")
    
    # Test general search
    print("\n1. Testing general search...")
    result = agent_search(session, "alice", "machine learning")
    print_result("agent_search(alice, 'machine learning')", result)
    
    # Test case-insensitive search
    print("\n2. Testing case-insensitive search...")
    result2 = agent_search(session, "alice", "MACHINE LEARNING")
    print_result("agent_search(alice, 'MACHINE LEARNING')", result2)
    
    # Test user-specific search
    print("\n3. Testing user search...")
    result3 = agent_search(session, "alice", "alice", "users")
    print_result("agent_search(alice, 'alice', 'users')", result3)
    
    # Test post-specific search
    print("\n4. Testing post search...")
    result4 = agent_search(session, "alice", "introduction", "posts")
    print_result("agent_search(alice, 'introduction', 'posts')", result4)
    
    # Test empty search (should fail)
    print("\n5. Testing empty search...")
    result5 = agent_search(session, "alice", "tech")
    print_result("agent_search(alice, 'tech')", result5)

def test_social_services(session, _users):
    """Test SOCIAL SERVICES"""
    print_test_header("SOCIAL SERVICES")
    
    # Test following
    print("\n1. Testing follow relationships...")
    follow_pairs = [
        ("alice", "bob"),
        ("alice", "charlie"),
        ("bob", "diana"),
        ("charlie", "alice")
    ]
    
    for follower, followed in follow_pairs:
        result = agent_connect_with_user(session, follower, "follow", followed)
        print_result(f"agent_connect_with_user({follower}, follow, {followed})", result)
    
    # Test unfollowing
    print("\n2. Testing unfollow relationships...")
    if len(follow_pairs) > 0:
        result = agent_connect_with_user(session, "alice", "unfollow", "charlie")
        print_result("agent_connect_with_user(alice, unfollow, charlie)", result)
    
    # Test community creation
    print("\n3. Testing community creation...")
    communities = [
        ("alice", "Tech Enthusiasts", "A community for people passionate about technology and innovation"),
        ("bob", "Data Science Club", "Discuss the latest trends in data science and analytics"),
        ("charlie", "Philosophy Forum", "Explore deep questions about life, existence, and knowledge")
    ]
    
    created_communities = []
    for creator, name, description in communities:
        result = agent_manage_community(session, creator, "create", name, description)
        print_result(f"agent_manage_community({creator}, create, {name})", result)
        if result["success"]:
            created_communities.append((name, description))
    
    # Test community joining
    print("\n4. Testing community joining...")
    join_operations = [
        ("bob", "Tech Enthusiasts"),
        ("charlie", "Tech Enthusiasts"),
        ("alice", "Data Science Club"),
        ("diana", "Data Science Club"),
        ("diana", "Philosophy Forum")
    ]
    
    for username, community_name in join_operations:
        result = agent_manage_community(session, username, "join", community_name)
        print_result(f"agent_manage_community({username}, join, {community_name})", result)
    
    # Test community info
    print("\n5. Testing community info...")
    if len(created_communities) > 0:
        result = agent_manage_community(session, "alice", "get_info", "Tech Enthusiasts")
        print_result("agent_manage_community(alice, get_info, Tech Enthusiasts)", result)
    
    # Test community members
    print("\n6. Testing community members...")
    if len(created_communities) > 0:
        result = agent_manage_community(session, "alice", "get_members", "Tech Enthusiasts")
        print_result("agent_manage_community(alice, get_members, Tech Enthusiasts)", result)
    
    # Test leaving community
    print("\n7. Testing leaving community...")
    result = agent_manage_community(session, "charlie", "leave", "Tech Enthusiasts")
    print_result("agent_manage_community(charlie, leave, Tech Enthusiasts)", result)

def main():
    """Main test runner"""
    print("🚀 Starting comprehensive services test...")
    
    # Initialize database
    test_db_path = "test_comprehensive_services.db"
    db = initialize_database(test_db_path)
    
    try:
        with db.get_session() as session:
            # Test all services
            users = test_user_services(session)
            posts = test_content_services(session, users)
            test_algorithm_services(session, users)
            test_search_services(session, users)
            test_social_services(session, users)
            
            print(f"\n{'='*60}")
            print("🎉 ALL TESTS COMPLETED!")
            print(f"{'='*60}")
            print(f"📊 Summary:")
            print(f"   Users created: {len(users)}")
            print(f"   Posts created: {len(posts)}")
            print(f"   Services tested: 5 categories")
            print(f"   Database: {test_db_path}")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Close database
        db.close()
        
        # Ask user if they want to keep the test database
        keep_db = input(f"\nKeep test database '{test_db_path}'? (y/N): ").strip().lower()
        if keep_db != 'y':
            Path(test_db_path).unlink(missing_ok=True)
            print("🗑️  Test database cleaned up.")
        else:
            print(f"💾 Test database saved as '{test_db_path}'")

if __name__ == "__main__":
    main()