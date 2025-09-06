"""
Business-level social media functions.

High-level social media operations that compose atomic operations into complete actions.
Used by platform/, agents/, and analysis/ modules for standard social media behaviors.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from . import operations as _ops

# ============================================================================
# USER SERVICES
# ============================================================================

def create_user_account(
    session: Session,
    username: str,
    display_name: Optional[str] = None,
    bio: Optional[str] = None
) -> dict:
    """Create a new user account."""
    try:
        user = _ops.create_user(session, username, display_name, bio)
        profile = get_user_profile(session, username)
        
        return {
            "success": True,
            "message": f"User @{username} created successfully",
            "data": profile
        }
    except _ops.DuplicateError as e:
        return {
            "success": False,
            "message": str(e),
            "data": None
        }

def get_user_profile(session: Session, username: str) -> Optional[dict]:
    """Get user profile with computed stats."""
    user = _ops.get_user_by_username(session, username)
    if not user:
        return None
    
    # Get computed stats
    posts = _ops.get_posts_by_user(session, user.id, limit=1000, include_comments=False)
    followers = _ops.get_followers(session, user.id)
    following = _ops.get_following(session, user.id)
    
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "bio": user.bio,
        "created_at": user.created_at.isoformat(),
        "follower_count": len(followers),
        "following_count": len(following),
        "post_count": len(posts)
    }

def get_user_stats(session: Session, username: str) -> Optional[dict]:
    """Get detailed user statistics."""
    user = _ops.get_user_by_username(session, username)
    if not user:
        return None
    
    all_posts = _ops.get_posts_by_user(session, user.id, limit=10000, include_comments=True)
    posts_only = [p for p in all_posts if not p.is_comment]
    comments_only = [p for p in all_posts if p.is_comment]
    
    followers = _ops.get_followers(session, user.id)
    following = _ops.get_following(session, user.id)
    
    # Calculate total likes received across all posts
    total_likes = 0
    for post in posts_only:
        reaction_counts = _ops.get_reaction_counts(session, post.id)
        total_likes += reaction_counts.get("like", 0)
    
    return {
        "username": username,
        "total_posts": len(posts_only),
        "total_comments": len(comments_only),
        "total_followers": len(followers),
        "total_following": len(following),
        "total_likes_received": total_likes,
        "join_date": user.created_at.isoformat()
    }

# ============================================================================
# CONTENT SERVICES
# ============================================================================

def create_user_post(
    session: Session,
    username: str,
    content: str,
    title: Optional[str] = None
) -> dict:
    """Create a new post for a user."""
    try:
        user = _ops.get_user_by_username(session, username)
        if not user:
            return {
                "success": False,
                "message": f"User @{username} not found",
                "data": None
            }
        
        post = _ops.create_post(session, user.id, content, title=title)
        post_data = _format_post_data(session, post)
        
        return {
            "success": True,
            "message": f"Post created successfully (ID: {post.id})",
            "data": post_data
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to create post: {str(e)}",
            "data": None
        }

def create_comment(
    session: Session,
    username: str,
    post_id: int,
    content: str
) -> dict:
    """Create a comment on a post."""
    try:
        user = _ops.get_user_by_username(session, username)
        if not user:
            return {
                "success": False,
                "message": f"User @{username} not found",
                "data": None
            }
        
        comment = _ops.create_post(session, user.id, content, parent_post_id=post_id)
        comment_data = _format_post_data(session, comment)
        
        return {
            "success": True,
            "message": f"Comment created successfully (ID: {comment.id})",
            "data": comment_data
        }
    except _ops.PostNotFoundError:
        return {
            "success": False,
            "message": f"Post {post_id} not found",
            "data": None
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to create comment: {str(e)}",
            "data": None
        }

# Import feed algorithm from dedicated module
from . import feed_algorithm

def get_user_feed(
    session: Session,
    username: str,
    limit: int = 20
) -> List[dict]:
    """
    Get personalized feed for a user.
    
    This function delegates to the sophisticated feed algorithm
    in the dedicated feed_algorithm module.
    """
    return feed_algorithm.get_user_feed(session, username, limit)

def get_post_details(session: Session, post_id: int) -> Optional[dict]:
    """Get detailed information about a specific post."""
    post = _ops.get_post_by_id(session, post_id)
    if not post:
        return None
    
    return _format_post_data(session, post)

def get_post_by_title(session: Session, title: str) -> Optional[dict]:
    """Get detailed information about a specific post by title."""
    post = _ops.get_post_by_title(session, title)
    if not post:
        return None
    
    return _format_post_data(session, post)

def get_trending_posts(session: Session, limit: int = 10) -> List[dict]:
    """Get trending posts."""
    # For MVP, just get recent posts with highest like counts
    # TODO: More sophisticated trending algorithm in platform/trending.py
    
    from sqlalchemy import func, desc, and_
    from datetime import timedelta
    from .models import Post, Reaction
    
    # Get posts from last 24 hours with like counts
    recent_cutoff = datetime.now() - timedelta(days=1)
    
    trending_query = session.query(
        Post,
        func.count(Reaction.id).label('like_count')
    ).outerjoin(
        Reaction,
        and_(
            Reaction.post_id == Post.id,
            Reaction.reaction_type == 'like',
            Reaction.deleted_at.is_(None)
        )
    ).filter(
        and_(
            Post.created_at >= recent_cutoff,
            Post.deleted_at.is_(None),
            Post.parent_post_id.is_(None)  # Only top-level posts
        )
    ).group_by(Post.id).order_by(desc('like_count')).limit(limit)
    
    trending_posts = []
    for post, like_count in trending_query.all():
        post_data = _format_post_data(session, post)
        trending_posts.append(post_data)
    
    return trending_posts

# ============================================================================
# SOCIAL SERVICES
# ============================================================================

def follow_user(
    session: Session,
    follower_username: str,
    followed_username: str
) -> dict:
    """Create a follow relationship."""
    try:
        follower = _ops.get_user_by_username(session, follower_username)
        followed = _ops.get_user_by_username(session, followed_username)
        
        if not follower:
            return {
                "success": False,
                "message": f"User @{follower_username} not found",
                "data": None
            }
        
        if not followed:
            return {
                "success": False,
                "message": f"User @{followed_username} not found",
                "data": None
            }
        
        if follower.id == followed.id:
            return {
                "success": False,
                "message": "Cannot follow yourself",
                "data": None
            }
        
        _ops.create_relationship(session, follower.id, followed.id, "follow")
        
        # Get updated counts
        following_count = len(_ops.get_following(session, follower.id))
        
        return {
            "success": True,
            "message": f"@{follower_username} is now following @{followed_username}",
            "data": {"following_count": following_count}
        }
    except _ops.DuplicateError:
        return {
            "success": False,
            "message": f"@{follower_username} is already following @{followed_username}",
            "data": None
        }

def unfollow_user(
    session: Session,
    follower_username: str,
    followed_username: str
) -> dict:
    """Remove a follow relationship."""
    try:
        follower = _ops.get_user_by_username(session, follower_username)
        followed = _ops.get_user_by_username(session, followed_username)
        
        if not follower or not followed:
            return {
                "success": False,
                "message": "One or both users not found",
                "data": None
            }
        
        relationship = _ops.soft_delete_relationship(session, follower.id, followed.id, "follow")
        
        if relationship:
            following_count = len(_ops.get_following(session, follower.id))
            return {
                "success": True,
                "message": f"@{follower_username} unfollowed @{followed_username}",
                "data": {"following_count": following_count}
            }
        else:
            return {
                "success": False,
                "message": f"@{follower_username} was not following @{followed_username}",
                "data": None
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to unfollow: {str(e)}",
            "data": None
        }

def like_post(
    session: Session,
    username: str,
    post_id: int
) -> dict:
    """Like a post."""
    try:
        user = _ops.get_user_by_username(session, username)
        if not user:
            return {
                "success": False,
                "message": f"User @{username} not found",
                "data": None
            }
        
        _ops.create_reaction(session, user.id, post_id, "like")
        
        # Get updated reaction counts
        reaction_counts = _ops.get_reaction_counts(session, post_id)
        
        return {
            "success": True,
            "message": f"@{username} liked post {post_id}",
            "data": {"reaction_counts": reaction_counts}
        }
    except _ops.PostNotFoundError:
        return {
            "success": False,
            "message": f"Post {post_id} not found",
            "data": None
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to like post: {str(e)}",
            "data": None
        }

def unlike_post(
    session: Session,
    username: str,
    post_id: int
) -> dict:
    """Remove like from a post."""
    try:
        user = _ops.get_user_by_username(session, username)
        if not user:
            return {
                "success": False,
                "message": f"User @{username} not found",
                "data": None
            }
        
        reaction = _ops.soft_delete_reaction(session, user.id, post_id, "like")
        
        if reaction:
            reaction_counts = _ops.get_reaction_counts(session, post_id)
            return {
                "success": True,
                "message": f"@{username} unliked post {post_id}",
                "data": {"reaction_counts": reaction_counts}
            }
        else:
            return {
                "success": False,
                "message": f"@{username} had not liked post {post_id}",
                "data": None
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to unlike post: {str(e)}",
            "data": None
        }

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _format_post_data(session: Session, post) -> dict:
    """Convert database Post object to dict format."""
    # Get author info
    author = _ops.get_user_by_id(session, post.user_id)
    
    # Get comment count
    comments = _ops.get_comments_for_post(session, post.id)
    
    # Get reaction counts
    reaction_counts = _ops.get_reaction_counts(session, post.id)
    
    return {
        "id": post.id,
        "title": post.title,
        "author_username": author.username if author else "unknown",
        "author_display_name": author.display_name if author else None,
        "content": post.content,
        "created_at": post.created_at.isoformat(),
        "is_comment": post.is_comment,
        "parent_post_id": post.parent_post_id,
        "comment_count": len(comments),
        "reaction_counts": reaction_counts
    }

if __name__ == "__main__":
    # Quick test of services
    from .connection import initialize_database
    
    print("Testing services...")
    db = initialize_database("test_services.db")
    
    with db.get_session() as session:
        # Test user creation
        result = create_user_account(session, "alice", "Alice Smith")
        print(f"Create user: {result['message']}")
        
        # Test posting
        result = create_user_post(session, "alice", "Hello, world! This is my first post.")
        print(f"Create post: {result['message']}")
        
        # Test user profile
        profile = get_user_profile(session, "alice")
        print(f"User profile: @{profile['username']} has {profile['post_count']} posts")
    
    db.close()
    
    # Clean up
    from pathlib import Path
    Path("test_services.db").unlink(missing_ok=True)
    
    print("Services test completed!")