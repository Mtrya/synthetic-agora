"""
Business-level social media functions.

High-level social media operations that compose atomic operations into complete actions.
Used by platform/, agents/, and analysis/ modules for standard social media behaviors.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from . import operations as _ops

# ============================================================================
# USER SERVICES
# ============================================================================

def create_user_account(
    session: Session,
    username: str,
    bio: Optional[str] = None
) -> dict:
    """Create a new user account."""
    try:
        user = _ops.create_user(session, username, bio)
        
        # For new user creation, use username as both agent and target
        profile_result = _agent_get_user_profile(session, username, username)
        
        return {
            "success": True,
            "message": f"User @{username} created successfully",
            "data": profile_result["data"] if profile_result["success"] else None
        }
    except _ops.DuplicateError as e:
        return {
            "success": False,
            "message": str(e),
            "data": None
        }

# ============================================================================
# CONTENT CREATE
# ============================================================================

def agent_create_post(
    session: Session,
    agent_username: str,
    title: str,
    content: str
) -> dict:
    """Create a new post for a user."""
    try:
        # Validate inputs
        if not title or not title.strip():
            return {
                "success": False,
                "message": "Title cannot be empty",
                "data": None
            }
        if not content or not content.strip():
            return {
                "success": False,
                "message": "Content cannot be empty",
                "data": None
            }
        
        user = _ops.get_user_by_username(session, agent_username)
        if not user:
            return {
                "success": False,
                "message": f"User @{agent_username} not found",
                "data": None
            }
        
        post = _ops.create_post(session, user.id, content, title=title.strip())
        
        return {
            "success": True,
            "message": f"Post created successfully (ID: {post.id})",
            "data": {
                "agent_username": agent_username,
                "title": post.title,
                "content": post.content,
                "created_at": post.created_at.isoformat()
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to create post: {str(e)}",
            "data": None
        }

def _agent_create_comment(
    session: Session,
    agent_username: str,
    post_id: int,
    content: str
) -> dict:
    """Create a comment on a post."""
    try:
        # Validate inputs
        if not content or not content.strip():
            return {
                "success": False,
                "message": "Content cannot be empty",
                "data": None
            }
        
        user = _ops.get_user_by_username(session, agent_username)
        if not user:
            return {
                "success": False,
                "message": f"User @{agent_username} not found",
                "data": None
            }
        
        # Validate post exists and is not deleted
        parent_post = _ops.get_post_by_id(session, post_id)
        if not parent_post or parent_post.deleted_at:
            return {
                "success": False,
                "message": f"Post {post_id} not found",
                "data": None
            }
        
        comment = _ops.create_post(session, user.id, content.strip(), parent_post_id=post_id)
        
        return {
            "success": True,
            "message": f"Comment created successfully (ID: {comment.id})",
            "data": {
                "agent_username": agent_username,
                "post_title": parent_post.title,
                "comment_content": comment.content,
                "created_at": comment.created_at.isoformat()
            }
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

def _agent_create_reply(
    session: Session,
    agent_username: str,
    post_id: int,
    content: str
) -> dict:
    """Create a reply to a comment or another reply."""
    try:
        # Validate inputs
        if not content or not content.strip():
            return {
                "success": False,
                "message": "Content cannot be empty",
                "data": None
            }
        
        user = _ops.get_user_by_username(session, agent_username)
        if not user:
            return {
                "success": False,
                "message": f"User @{agent_username} not found",
                "data": None
            }
        
        # Validate parent post exists and is not deleted
        parent_post = _ops.get_post_by_id(session, post_id)
        if not parent_post or parent_post.deleted_at:
            return {
                "success": False,
                "message": f"Post {post_id} not found",
                "data": None
            }
        
        # Validate parent is a comment or reply (has parent_post_id)
        if not parent_post.parent_post_id:
            return {
                "success": False,
                "message": f"Post {post_id} is not a comment or reply, cannot reply to it",
                "data": None
            }
        
        reply = _ops.create_post(session, user.id, content.strip(), parent_post_id=post_id)
        
        # Get the content of the parent comment/reply
        parent_content = parent_post.content
        
        return {
            "success": True,
            "message": f"Reply created successfully (ID: {reply.id})",
            "data": {
                "agent_username": agent_username,
                "parent_content": parent_content,
                "reply_content": reply.content,
                "created_at": reply.created_at.isoformat()
            }
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
            "message": f"Failed to create reply: {str(e)}",
            "data": None
        }

def agent_create_response(
    session: Session,
    agent_username: str,
    content_type: str,
    post_id: int,
    content: str
) -> dict:
    """Unified content creation for comments and replies."""
    if content_type == "comment":
        return _agent_create_comment(session, agent_username, post_id, content)
    elif content_type == "reply":
        return _agent_create_reply(session, agent_username, post_id, content)
    else:
        return {
            "success": False,
            "message": f"Invalid content_type: {content_type}. Use 'comment' or 'reply'",
            "data": None
        }

# ============================================================================
# CONTENT VIEW
# ============================================================================

def _agent_get_post_overview(
    session: Session,
    agent_username: str,
    post_id: int
) -> dict:
    """Get comprehensive overview of a post with reactions and top comments."""
    try:
        # Validate post exists and is not deleted
        post = _ops.get_post_by_id(session, post_id)
        if not post or post.deleted_at:
            return {
                "success": False,
                "message": f"Post {post_id} not found",
                "data": None
            }
        
        # Get author info
        author = _ops.get_user_by_id(session, post.user_id)
        author_username = author.username if author else "unknown"
        
        # Get reaction counts
        reaction_counts = _ops.get_reaction_counts(session, post_id)
        like_count = reaction_counts.get("like", 0)
        dislike_count = reaction_counts.get("dislike", 0)
        
        # Get all comments and replies for counting
        all_comments = _ops.get_comments_for_post(session, post_id)
        comment_count = len(all_comments)
        
        # Get top 20 comments (excluding replies) with their content
        top_comments = []
        for comment in all_comments[:20]:
            if not comment.parent_post_id:  # Only top-level comments
                comment_author = _ops.get_user_by_id(session, comment.user_id)
                top_comments.append({
                    "content": comment.content,
                    "author": comment_author.username if comment_author else "unknown",
                    "created_at": comment.created_at.isoformat()
                })
        
        return {
            "success": True,
            "message": f"Retrieved overview for post {post_id}",
            "data": {
                "title": post.title,
                "author_username": author_username,
                "content": post.content,
                "created_at": post.created_at.isoformat(),
                "like_count": like_count,
                "dislike_count": dislike_count,
                "comment_count": comment_count,
                "top_comments": top_comments
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get post overview: {str(e)}",
            "data": None
        }

def _agent_get_post_reactions(
    session: Session,
    agent_username: str,
    post_id: int
) -> dict:
    """Get reaction information for a post showing who liked/disliked."""
    try:
        # Validate post exists and is not deleted
        post = _ops.get_post_by_id(session, post_id)
        if not post or post.deleted_at:
            return {
                "success": False,
                "message": f"Post {post_id} not found",
                "data": None
            }
        
        # Get all reactions for this post
        all_reactions = _ops.get_post_reactions(session, post_id)
        
        # Separate likes and dislikes
        like_usernames = []
        dislike_usernames = []
        
        for reaction in all_reactions:
            user = _ops.get_user_by_id(session, reaction.user_id)
            if user:
                if reaction.reaction_type == "like":
                    like_usernames.append(user.username)
                elif reaction.reaction_type == "dislike":
                    dislike_usernames.append(user.username)
        
        return {
            "success": True,
            "message": f"Retrieved reactions for post {post_id}",
            "data": {
                "title": post.title,
                "likes": like_usernames,
                "dislikes": dislike_usernames
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get post reactions: {str(e)}",
            "data": None
        }

def _agent_get_post_comment_section(
    session: Session,
    agent_username: str,
    post_id: int
) -> dict:
    """Get nested comment structure with replies for a post."""
    try:
        # Validate post exists and is not deleted
        post = _ops.get_post_by_id(session, post_id)
        if not post or post.deleted_at:
            return {
                "success": False,
                "message": f"Post {post_id} not found",
                "data": None
            }
        
        # Get all comments and replies
        all_comments = _ops.get_comments_for_post(session, post_id)
        
        # Build nested structure
        comments_by_parent = {}
        root_comments = []
        
        # First pass: organize by parent
        for comment in all_comments:
            author = _ops.get_user_by_id(session, comment.user_id)
            comment_data = {
                "content": comment.content,
                "author": author.username if author else "unknown",
                "created_at": comment.created_at.isoformat(),
                "replies": []
            }
            
            if comment.parent_post_id == post_id:
                # This is a root comment on the post
                root_comments.append(comment_data)
                comments_by_parent[comment.id] = comment_data
            else:
                # This is a reply to another comment
                comments_by_parent[comment.id] = comment_data
        
        # Second pass: build reply hierarchy
        for comment in all_comments:
            if comment.parent_post_id != post_id:
                # This is a reply, find its parent
                parent_data = comments_by_parent.get(comment.parent_post_id)
                if parent_data:
                    comment_data = comments_by_parent[comment.id]
                    parent_data["replies"].append(comment_data)
        
        return {
            "success": True,
            "message": f"Retrieved comment section for post {post_id}",
            "data": {
                "title": post.title,
                "comments": root_comments
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get comment section: {str(e)}",
            "data": None
        }

def agent_view_post(
    session: Session,
    agent_username: str,
    view_type: str,
    post_id: int
) -> dict:
    """Unified post viewing operations."""
    if view_type == "overview":
        return _agent_get_post_overview(session, agent_username, post_id)
    elif view_type == "reactions":
        return _agent_get_post_reactions(session, agent_username, post_id)
    elif view_type == "comments":
        return _agent_get_post_comment_section(session, agent_username, post_id)
    else:
        return {
            "success": False,
            "message": f"Invalid view_type: {view_type}. Use 'overview', 'reactions', or 'comments'",
            "data": None
        }

# ============================================================================
# CONTENT REACT
# ============================================================================

def _agent_like_post(
    session: Session,
    agent_username: str,
    post_id: int
) -> dict:
    """Like a post."""
    try:
        agent = _ops.get_user_by_username(session, agent_username)
        if not agent:
            return {
                "success": False,
                "message": f"Agent @{agent_username} not found",
                "data": None
            }
        
        # Validate post exists and is not deleted
        post = _ops.get_post_by_id(session, post_id)
        if not post:
            return {
                "success": False,
                "message": f"Post {post_id} not found",
                "data": None
            }
        
        if post.deleted_at is not None:
            return {
                "success": False,
                "message": f"Post {post_id} has been deleted",
                "data": None
            }
        
        if post.is_comment:
            return {
                "success": False,
                "message": f"Post {post_id} is a comment, use like_comment instead",
                "data": None
            }
        
        _ops.create_reaction(session, agent.id, post_id, "like")
        
        # Get post author info
        author = _ops.get_user_by_id(session, post.user_id)
        author_username = author.username if author else "unknown"
        
        return {
            "success": True,
            "message": f"@{agent_username} liked post '{post.title}' by @{author_username}",
            "data": {
                "agent_username": agent_username,
                "post_title": post.title,
                "post_author": author_username
            }
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

def _agent_unlike_post(
    session: Session,
    agent_username: str,
    post_id: int
) -> dict:
    """Remove like from a post."""
    try:
        agent = _ops.get_user_by_username(session, agent_username)
        if not agent:
            return {
                "success": False,
                "message": f"Agent @{agent_username} not found",
                "data": None
            }
        
        # Validate post exists and is not deleted
        post = _ops.get_post_by_id(session, post_id)
        if not post:
            return {
                "success": False,
                "message": f"Post {post_id} not found",
                "data": None
            }
        
        if post.deleted_at is not None:
            return {
                "success": False,
                "message": f"Post {post_id} has been deleted",
                "data": None
            }
        
        if post.is_comment:
            return {
                "success": False,
                "message": f"Post {post_id} is a comment, use unlike_comment instead",
                "data": None
            }
        
        reaction = _ops.soft_delete_reaction(session, agent.id, post_id, "like")
        
        if reaction:
            # Get post author info
            author = _ops.get_user_by_id(session, post.user_id)
            author_username = author.username if author else "unknown"
            
            return {
                "success": True,
                "message": f"@{agent_username} unliked post '{post.title}' by @{author_username}",
                "data": {
                    "agent_username": agent_username,
                    "post_title": post.title,
                    "post_author": author_username
                }
            }
        else:
            return {
                "success": False,
                "message": f"@{agent_username} had not liked post {post_id}",
                "data": None
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to unlike post: {str(e)}",
            "data": None
        }

def _agent_share_post(
    session: Session,
    agent_username: str,
    post_id: int,
    comment: Optional[str] = None
) -> dict:
    """Share a post by creating a new post with reference to the original."""
    try:
        # Validate post exists and is not deleted
        original_post = _ops.get_post_by_id(session, post_id)
        if not original_post or original_post.deleted_at:
            return {
                "success": False,
                "message": f"Post {post_id} not found",
                "data": None
            }
        
        # Validate that it's a post (not a comment/reply)
        if original_post.parent_post_id:
            return {
                "success": False,
                "message": f"Post {post_id} is a comment or reply, cannot share it",
                "data": None
            }
        
        # Get original author info
        original_author = _ops.get_user_by_id(session, original_post.user_id)
        original_author_username = original_author.username if original_author else "unknown"
        
        # Get the sharing user
        sharing_user = _ops.get_user_by_username(session, agent_username)
        if not sharing_user:
            return {
                "success": False,
                "message": f"User @{agent_username} not found",
                "data": None
            }
        
        # Create human-readable share content
        from datetime import datetime
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # Build content with comment if provided
        if comment and comment.strip():
            share_content = f"""{comment.strip()}

🔄 Shared Post

Original: "{original_post.title}" by @{original_author_username}
{original_post.content}

---
Shared by @{agent_username} at {current_time}"""
        else:
            share_content = f"""🔄 Shared Post

Original: "{original_post.title}" by @{original_author_username}
{original_post.content}

---
Shared by @{agent_username} at {current_time}"""
        
        # Set title: "Shared: {original_post.title}"
        share_title = f"Shared: {original_post.title}"
        
        # Create the shared post
        shared_post = _ops.create_post(session, sharing_user.id, share_content, title=share_title)
        
        return {
            "success": True,
            "message": f"Post shared successfully (ID: {shared_post.id})",
            "data": {
                "agent_username": agent_username,
                "shared_post_title": shared_post.title,
                "created_at": shared_post.created_at.isoformat(),
                "original_post_title": original_post.title,
                "original_post_author": original_author_username,
                "original_post_created_at": original_post.created_at.isoformat()
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to share post: {str(e)}",
            "data": None
        }

def _agent_like_comment(
    session: Session,
    agent_username: str,
    post_id: int
) -> dict:
    """Like a comment or reply."""
    try:
        agent = _ops.get_user_by_username(session, agent_username)
        if not agent:
            return {
                "success": False,
                "message": f"Agent @{agent_username} not found",
                "data": None
            }
        
        # Validate post exists and is not deleted
        post = _ops.get_post_by_id(session, post_id)
        if not post:
            return {
                "success": False,
                "message": f"Comment {post_id} not found",
                "data": None
            }
        
        if post.deleted_at is not None:
            return {
                "success": False,
                "message": f"Comment {post_id} has been deleted",
                "data": None
            }
        
        if not post.is_comment:
            return {
                "success": False,
                "message": f"Post {post_id} is not a comment, use like_post instead",
                "data": None
            }
        
        _ops.create_reaction(session, agent.id, post_id, "like")
        
        # Get comment author info
        author = _ops.get_user_by_id(session, post.user_id)
        author_username = author.username if author else "unknown"
        
        return {
            "success": True,
            "message": f"@{agent_username} liked comment by @{author_username}",
            "data": {
                "agent_username": agent_username,
                "comment_content": post.content,
                "comment_author": author_username
            }
        }
    except _ops.PostNotFoundError:
        return {
            "success": False,
            "message": f"Comment {post_id} not found",
            "data": None
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to like comment: {str(e)}",
            "data": None
        }

def _agent_unlike_comment(
    session: Session,
    agent_username: str,
    post_id: int
) -> dict:
    """Remove like from a comment or reply."""
    try:
        agent = _ops.get_user_by_username(session, agent_username)
        if not agent:
            return {
                "success": False,
                "message": f"Agent @{agent_username} not found",
                "data": None
            }
        
        # Validate post exists and is not deleted
        post = _ops.get_post_by_id(session, post_id)
        if not post:
            return {
                "success": False,
                "message": f"Comment {post_id} not found",
                "data": None
            }
        
        if post.deleted_at is not None:
            return {
                "success": False,
                "message": f"Comment {post_id} has been deleted",
                "data": None
            }
        
        if not post.is_comment:
            return {
                "success": False,
                "message": f"Post {post_id} is not a comment, use unlike_post instead",
                "data": None
            }
        
        reaction = _ops.soft_delete_reaction(session, agent.id, post_id, "like")
        
        if reaction:
            # Get comment author info
            author = _ops.get_user_by_id(session, post.user_id)
            author_username = author.username if author else "unknown"
            
            return {
                "success": True,
                "message": f"@{agent_username} unliked comment by @{author_username}",
                "data": {
                    "agent_username": agent_username,
                    "comment_content": post.content,
                    "comment_author": author_username
                }
            }
        else:
            return {
                "success": False,
                "message": f"@{agent_username} had not liked comment {post_id}",
                "data": None
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to unlike comment: {str(e)}",
            "data": None
        }

def agent_react_to_post(
    session: Session,
    agent_username: str,
    reaction_type: str,
    post_id: int,
    comment: Optional[str] = None
) -> dict:
    """Unified post reactions: like, unlike, share."""
    if reaction_type == "like":
        return _agent_like_post(session, agent_username, post_id)
    elif reaction_type == "unlike":
        return _agent_unlike_post(session, agent_username, post_id)
    elif reaction_type == "share":
        if not comment:
            return {
                "success": False,
                "message": f"comment is required for 'share' action",
                "data": None
            }
        return _agent_share_post(session, agent_username, post_id, comment)
    else:
        return {
            "success": False,
            "message": f"Invalid reaction_type: {reaction_type}. Use 'like', 'unlike', or 'share'",
            "data": None
        }

def agent_react_to_response(
    session: Session,
    agent_username: str,
    reaction_type: str,
    post_id: int
) -> dict:
    """Unified comment reactions: like, unlike."""
    if reaction_type == "like":
        return _agent_like_comment(session, agent_username, post_id)
    elif reaction_type == "unlike":
        return _agent_unlike_comment(session, agent_username, post_id)
    else:
        return {
            "success": False,
            "message": f"Invalid reaction_type: {reaction_type}. Use 'like' or 'unlike'",
            "data": None
        }

# ============================================================================
# SOCIAL CONNECT
# ============================================================================

def _agent_get_user_profile(session: Session, agent_username: str, target_username: str) -> dict:
    """Get comprehensive user profile with stats and top posts."""
    # Get target user
    target_user = _ops.get_user_by_username(session, target_username)
    if not target_user:
        return {
            "success": False,
            "message": f"User @{target_username} not found",
            "data": None
        }
    
    # Get basic stats
    posts = _ops.get_posts_by_user(session, target_user.id, limit=1000, include_comments=False)
    followers = _ops.get_followers(session, target_user.id)
    following = _ops.get_following(session, target_user.id)
    
    # Calculate likes received and given
    likes_received = 0
    for post in posts:
        reaction_counts = _ops.get_reaction_counts(session, post.id)
        likes_received += reaction_counts.get("like", 0)
    
    # Get likes given by user
    agent_user = _ops.get_user_by_username(session, agent_username)
    likes_given = 0
    if agent_user:
        user_reactions = _ops.get_user_reactions(session, agent_user.id)
        likes_given = sum(1 for r in user_reactions if r.reaction_type == "like")
    
    # Get top 4 most liked posts (excluding comments)
    posts_with_likes = []
    for post in posts:
        reaction_counts = _ops.get_reaction_counts(session, post.id)
        like_count = reaction_counts.get("like", 0)
        if like_count > 0 and post.title:  # Only include posts with titles and likes
            posts_with_likes.append((post.title, like_count))
    
    # Sort by like count and take top 4
    posts_with_likes.sort(key=lambda x: x[1], reverse=True)
    top_liked_posts = [title for title, _ in posts_with_likes[:4]]
    
    return {
        "success": True,
        "message": f"Retrieved profile for @{target_username}",
        "data": {
            "agent_username": agent_username,
            "target_username": target_username,
            "bio": target_user.bio or "",
            "follower_count": len(followers),
            "following_count": len(following),
            "post_count": len(posts),
            "likes_received": likes_received,
            "likes_given": likes_given,
            "top_liked_posts": top_liked_posts
        }
    }

def _agent_get_user_relationship(session: Session, agent_username: str, target_username: str) -> dict:
    """Get detailed relationship information between users."""
    # Get both users
    agent_user = _ops.get_user_by_username(session, agent_username)
    target_user = _ops.get_user_by_username(session, target_username)
    
    if not target_user:
        return {
            "success": False,
            "message": f"User @{target_username} not found",
            "data": None
        }
    
    if not agent_user:
        return {
            "success": False,
            "message": f"Agent user @{agent_username} not found",
            "data": None
        }
    
    # Get relationship data
    followers = _ops.get_followers(session, target_user.id)
    following = _ops.get_following(session, target_user.id)
    
    # Get friends (mutual follows)
    friends = []
    for follower in followers:
        if _ops.get_relationship(session, follower.id, target_user.id, "friend"):
            friends.append(follower.username)
    
    # Get agent's friends for mutual friend calculation
    agent_followers = _ops.get_followers(session, agent_user.id)
    agent_friends = []
    for follower in agent_followers:
        if _ops.get_relationship(session, follower.id, agent_user.id, "friend"):
            agent_friends.append(follower.username)
    
    # Find mutual friends
    mutual_friends = list(set(friends) & set(agent_friends))
    
    return {
        "success": True,
        "message": f"Retrieved relationship data for @{target_username}",
        "data": {
            "agent_username": agent_username,
            "target_username": target_username,
            "followers": [f.username for f in followers],
            "following": [f.username for f in following],
            "friends": friends,
            "mutual_friends": mutual_friends
        }
    }

def _agent_get_user_posts(session: Session, agent_username: str, target_username: str) -> dict:
    """Get recent posts from a user (excluding comments)."""
    # Get target user
    target_user = _ops.get_user_by_username(session, target_username)
    if not target_user:
        return {
            "success": False,
            "message": f"User @{target_username} not found",
            "data": None
        }
    
    # Get posts (excluding comments)
    posts = _ops.get_posts_by_user(session, target_user.id, limit=100, include_comments=False)
    
    # Extract titles, filtering out posts without titles
    post_titles = [post.title for post in posts if post.title]
    
    return {
        "success": True,
        "message": f"Retrieved {len(post_titles)} posts from @{target_username}",
        "data": {
            "agent_username": agent_username,
            "target_username": target_username,
            "post_titles": post_titles
        }
    }

def _agent_follow_user(
    session: Session,
    agent_username: str,
    target_username: str
) -> dict:
    """Create a follow relationship."""
    try:
        agent = _ops.get_user_by_username(session, agent_username)
        target = _ops.get_user_by_username(session, target_username)
        
        if not agent:
            return {
                "success": False,
                "message": f"Agent @{agent_username} not found",
                "data": None
            }
        
        if not target:
            return {
                "success": False,
                "message": f"Target user @{target_username} not found",
                "data": None
            }
        
        if agent.id == target.id:
            return {
                "success": False,
                "message": "Cannot follow yourself",
                "data": None
            }
        
        _ops.create_relationship(session, agent.id, target.id, "follow")
        
        return {
            "success": True,
            "message": f"@{agent_username} is now following @{target_username}",
            "data": {
                "agent_username": agent_username,
                "target_username": target_username
            }
        }
    except _ops.DuplicateError:
        return {
            "success": False,
            "message": f"@{agent_username} is already following @{target_username}",
            "data": None
        }

def _agent_unfollow_user(
    session: Session,
    agent_username: str,
    target_username: str
) -> dict:
    """Remove a follow relationship."""
    try:
        agent = _ops.get_user_by_username(session, agent_username)
        target = _ops.get_user_by_username(session, target_username)
        
        if not agent or not target:
            return {
                "success": False,
                "message": "One or both users not found",
                "data": None
            }
        
        relationship = _ops.soft_delete_relationship(session, agent.id, target.id, "follow")
        
        if relationship:
            return {
                "success": True,
                "message": f"@{agent_username} unfollowed @{target_username}",
                "data": {
                    "agent_username": agent_username,
                    "target_username": target_username
                }
            }
        else:
            return {
                "success": False,
                "message": f"@{agent_username} was not following @{target_username}",
                "data": None
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to unfollow: {str(e)}",
            "data": None
        }

def _agent_create_community(
    session: Session,
    agent_username: str,
    name: str,
    description: str
) -> dict:
    """Create a new community."""
    try:
        # Validate inputs
        if not name or not name.strip():
            return {
                "success": False,
                "message": "Community name cannot be empty",
                "data": None
            }
        
        if not description or not description.strip():
            return {
                "success": False,
                "message": "Community description cannot be empty",
                "data": None
            }
        
        # Check if community name already exists
        existing_community = _ops.get_community_by_name(session, name)
        if existing_community:
            return {
                "success": False,
                "message": f"Community '{name}' already exists",
                "data": None
            }
        
        # Get agent
        agent = _ops.get_user_by_username(session, agent_username)
        if not agent:
            return {
                "success": False,
                "message": f"Agent @{agent_username} not found",
                "data": None
            }
        
        # Create community
        community = _ops.create_community(session, name, agent.id, description)
        
        # Auto-join creator as admin
        _ops.create_membership(session, agent.id, community.id, "creator")
        
        return {
            "success": True,
            "message": f"@{agent_username} created community '{name}'",
            "data": {
                "agent_username": agent_username,
                "community_name": name,
                "description": description,
                "created_at": community.created_at.isoformat()
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to create community: {str(e)}",
            "data": None
        }

def _agent_join_community(
    session: Session,
    agent_username: str,
    community_name: str
) -> dict:
    """Join a community."""
    try:
        # Get agent
        agent = _ops.get_user_by_username(session, agent_username)
        if not agent:
            return {
                "success": False,
                "message": f"Agent @{agent_username} not found",
                "data": None
            }
        
        # Get community
        community = _ops.get_community_by_name(session, community_name)
        if not community:
            return {
                "success": False,
                "message": f"Community '{community_name}' not found",
                "data": None
            }
        
        if community.deleted_at is not None:
            return {
                "success": False,
                "message": f"Community '{community_name}' has been deleted",
                "data": None
            }
        
        # Check if already a member
        existing_membership = _ops.get_membership(session, agent.id, community.id)
        if existing_membership:
            return {
                "success": False,
                "message": f"@{agent_username} is already a member of '{community_name}'",
                "data": None
            }
        
        # Join community
        _ops.create_membership(session, agent.id, community.id, "member")
        
        return {
            "success": True,
            "message": f"@{agent_username} joined community '{community_name}'",
            "data": {
                "agent_username": agent_username,
                "community_name": community_name
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to join community: {str(e)}",
            "data": None
        }

def _agent_leave_community(
    session: Session,
    agent_username: str,
    community_name: str
) -> dict:
    """Leave a community."""
    try:
        # Get agent
        agent = _ops.get_user_by_username(session, agent_username)
        if not agent:
            return {
                "success": False,
                "message": f"Agent @{agent_username} not found",
                "data": None
            }
        
        # Get community
        community = _ops.get_community_by_name(session, community_name)
        if not community:
            return {
                "success": False,
                "message": f"Community '{community_name}' not found",
                "data": None
            }
        
        if community.deleted_at is not None:
            return {
                "success": False,
                "message": f"Community '{community_name}' has been deleted",
                "data": None
            }
        
        # Check if creator (cannot leave own community)
        if community.created_by == agent.id:
            return {
                "success": False,
                "message": f"@{agent_username} is the creator of '{community_name}' and cannot leave",
                "data": None
            }
        
        # Check membership
        membership = _ops.get_membership(session, agent.id, community.id)
        if not membership:
            return {
                "success": False,
                "message": f"@{agent_username} is not a member of '{community_name}'",
                "data": None
            }
        
        # Leave community (soft delete membership)
        from datetime import datetime, timezone
        membership.deleted_at = datetime.now(timezone.utc)
        session.flush()
        
        return {
            "success": True,
            "message": f"@{agent_username} left community '{community_name}'",
            "data": {
                "agent_username": agent_username,
                "community_name": community_name
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to leave community: {str(e)}",
            "data": None
        }

def _agent_get_community_infos(
    session: Session,
    agent_username: str,
    community_name: str
) -> dict:
    """Get community information with top members."""
    try:
        # Get agent
        agent = _ops.get_user_by_username(session, agent_username)
        if not agent:
            return {
                "success": False,
                "message": f"Agent @{agent_username} not found",
                "data": None
            }
        
        # Get community
        community = _ops.get_community_by_name(session, community_name)
        if not community:
            return {
                "success": False,
                "message": f"Community '{community_name}' not found",
                "data": None
            }
        
        if community.deleted_at is not None:
            return {
                "success": False,
                "message": f"Community '{community_name}' has been deleted",
                "data": None
            }
        
        # Get creator info
        creator = _ops.get_user_by_id(session, community.created_by)
        creator_username = creator.username if creator else "unknown"
        
        # Get all members
        members = _ops.get_community_members(session, community.id)
        
        # Get top 4 members (excluding creator, sorted by join date)
        top_members = []
        for member in members[:4]:  # First 4 members
            if member.id != community.created_by:  # Exclude creator
                top_members.append({
                    "username": member.username,
                    "bio": member.bio or ""
                })
        
        return {
            "success": True,
            "message": f"Retrieved info for community '{community_name}'",
            "data": {
                "agent_username": agent_username,
                "community_name": community.name,
                "description": community.description or "",
                "creator": creator_username,
                "top_members": top_members
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get community info: {str(e)}",
            "data": None
        }

def _agent_get_community_members(
    session: Session,
    agent_username: str,
    community_name: str
) -> dict:
    """Get all community members."""
    try:
        # Get agent
        agent = _ops.get_user_by_username(session, agent_username)
        if not agent:
            return {
                "success": False,
                "message": f"Agent @{agent_username} not found",
                "data": None
            }
        
        # Get community
        community = _ops.get_community_by_name(session, community_name)
        if not community:
            return {
                "success": False,
                "message": f"Community '{community_name}' not found",
                "data": None
            }
        
        if community.deleted_at is not None:
            return {
                "success": False,
                "message": f"Community '{community_name}' has been deleted",
                "data": None
            }
        
        # Get creator info
        creator = _ops.get_user_by_id(session, community.created_by)
        creator_username = creator.username if creator else "unknown"
        
        # Get all members
        members = _ops.get_community_members(session, community.id)
        
        # Format member list
        member_list = []
        for member in members:
            member_list.append({
                "username": member.username,
                "bio": member.bio or ""
            })
        
        return {
            "success": True,
            "message": f"Retrieved members for community '{community_name}'",
            "data": {
                "agent_username": agent_username,
                "community_name": community.name,
                "creator": creator_username,
                "members": member_list
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get community members: {str(e)}",
            "data": None
        }

def agent_connect_with_user(
    session: Session,
    agent_username: str,
    action_type: str,
    target_username: str
) -> dict:
    """Unified user operations: get_profile, get_relationship, get_posts, follow, unfollow."""
    if not target_username and action_type in ["get_profile", "get_relationship", "get_posts", "follow", "unfollow"]:
        return {
            "success": False,
            "message": f"target_username is required for action_type '{action_type}'",
            "data": None
        }
    
    if action_type == "get_profile":
        return _agent_get_user_profile(session, agent_username, target_username)
    elif action_type == "get_relationship":
        return _agent_get_user_relationship(session, agent_username, target_username)
    elif action_type == "get_posts":
        return _agent_get_user_posts(session, agent_username, target_username)
    elif action_type == "follow":
        return _agent_follow_user(session, agent_username, target_username)
    elif action_type == "unfollow":
        return _agent_unfollow_user(session, agent_username, target_username)
    else:
        return {
            "success": False,
            "message": f"Invalid action_type: {action_type}. Use 'profile', 'relationship', 'posts', 'follow', or 'unfollow'",
            "data": None
        }

def agent_manage_community(
    session: Session,
    agent_username: str,
    action_type: str,
    community_name: str,
    description: Optional[str] = None
) -> dict:
    """Unified community operations: create, join, leave, get_info, get_members."""
    if action_type == "create":
        if not community_name or not description:
            return {
                "success": False,
                "message": "community_name and description are required for 'create' action",
                "data": None
            }
        return _agent_create_community(session, agent_username, community_name, description)
    elif action_type in ["join", "leave", "get_info", "get_members"]:
        if not community_name:
            return {
                "success": False,
                "message": f"community_name is required for action_type '{action_type}'",
                "data": None
            }
        
        if action_type == "join":
            return _agent_join_community(session, agent_username, community_name)
        elif action_type == "leave":
            return _agent_leave_community(session, agent_username, community_name)
        elif action_type == "get_info":
            return _agent_get_community_infos(session, agent_username, community_name)
        elif action_type == "get_members":
            return _agent_get_community_members(session, agent_username, community_name)
    else:
        return {
            "success": False,
            "message": f"Invalid action_type: {action_type}. Use 'create', 'join', 'leave', 'info', or 'members'",
            "data": None
        }

# ============================================================================
# CONTENT DISCOVERY
# ============================================================================

def _agent_get_feed(
    session: Session,
    agent_username: str,
    limit: int = 20
) -> dict:
    """
    Get personalized feed for an agent.
    
    Simple MVP feed: posts from followed users + own posts + community posts,
    sorted by creation time (newest first).
    """
    try:
        # Get agent
        agent = _ops.get_user_by_username(session, agent_username)
        if not agent:
            return {
                "success": False,
                "message": f"Agent @{agent_username} not found",
                "data": None
            }
        
        # Get users this agent follows
        following = _ops.get_following(session, agent.id)
        following_ids = [u.id for u in following]
        
        # Include agent's own posts
        following_ids.append(agent.id)
        
        # Get communities agent is member of
        agent_communities = _ops.get_user_communities(session, agent.id)
        community_ids = [c.id for c in agent_communities]
        
        # Get posts from followed users (excluding comments)
        feed_posts = []
        for user_id in following_ids:
            user_posts = _ops.get_posts_by_user(session, user_id, limit=50, include_comments=False)
            feed_posts.extend(user_posts)
        
        # Get posts from agent's communities (excluding comments)
        for community_id in community_ids:
            community_members = _ops.get_community_members(session, community_id)
            for member in community_members:
                member_posts = _ops.get_posts_by_user(session, member.id, limit=10, include_comments=False)
                feed_posts.extend(member_posts)
        
        # Remove duplicates and sort by creation time (newest first)
        seen_posts = set()
        unique_posts = []
        for post in feed_posts:
            if post.id not in seen_posts:
                seen_posts.add(post.id)
                unique_posts.append(post)
        
        unique_posts.sort(key=lambda p: p.created_at, reverse=True)
        
        # Format posts for feed
        feed_items = []
        for post in unique_posts[:limit]:
            author = _ops.get_user_by_id(session, post.user_id)
            reaction_counts = _ops.get_reaction_counts(session, post.id)
            comments = _ops.get_comments_for_post(session, post.id)
            
            feed_items.append({
                "id": post.id,
                "title": post.title,
                "author_username": author.username if author else "unknown",
                "content": post.content,
                "created_at": post.created_at.isoformat(),
                "like_count": reaction_counts.get("like", 0),
                "comment_count": len(comments)
            })
        
        return {
            "success": True,
            "message": f"Retrieved feed for @{agent_username}",
            "data": {
                "agent_username": agent_username,
                "feed_items": feed_items
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get feed: {str(e)}",
            "data": None
        }

def _agent_get_trending(
    session: Session,
    agent_username: str,
    limit: int = 10
) -> dict:
    """
    Get trending posts globally.
    
    Simple MVP trending: posts from last 7 days with most likes,
    sorted by like count (highest first).
    """
    try:
        # Get agent
        agent = _ops.get_user_by_username(session, agent_username)
        if not agent:
            return {
                "success": False,
                "message": f"Agent @{agent_username} not found",
                "data": None
            }
        
        from sqlalchemy import func, desc, and_
        from datetime import timedelta
        from .models import Post, Reaction
        
        # Get posts from last 7 days with like counts
        recent_cutoff = datetime.now() - timedelta(days=7)
        
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
            # Get author info
            author = _ops.get_user_by_id(session, post.user_id)
            
            # Get comment count
            comments = _ops.get_comments_for_post(session, post.id)
            
            trending_posts.append({
                "id": post.id,
                "title": post.title,
                "author_username": author.username if author else "unknown",
                "content": post.content,
                "created_at": post.created_at.isoformat(),
                "like_count": like_count,
                "comment_count": len(comments)
            })
        
        return {
            "success": True,
            "message": f"Retrieved trending posts for @{agent_username}",
            "data": {
                "agent_username": agent_username,
                "trending_posts": trending_posts
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get trending posts: {str(e)}",
            "data": None
        }

def agent_get_discovery(
    session: Session,
    agent_username: str,
    discovery_type: str,
    limit: int = 20
) -> dict:
    """Unified content discovery: feed, trending."""
    if discovery_type == "feed":
        return _agent_get_feed(session, agent_username, limit)
    elif discovery_type == "trending":
        return _agent_get_trending(session, agent_username, limit)
    else:
        return {
            "success": False,
            "message": f"Invalid discovery_type: {discovery_type}. Use 'feed' or 'trending'",
            "data": None
        }

def agent_search(
    session: Session,
    agent_username: str,
    query: str,
    search_type: str = "all"
) -> dict:
    """Simple case-insensitive search across all content types.
    
    search_type: "all", "posts", "users", "communities"
    """
    try:
        # Validate inputs
        if not query or not query.strip():
            return {
                "success": False,
                "message": "Search query cannot be empty",
                "data": None
            }
        
        # Validate agent exists
        agent = _ops.get_user_by_username(session, agent_username)
        if not agent:
            return {
                "success": False,
                "message": f"Agent @{agent_username} not found",
                "data": None
            }
        
        query_lower = query.lower().strip()
        results = {"posts": [], "users": [], "communities": []}
        
        # Search posts
        if search_type in ["all", "posts"]:
            all_posts = _ops.get_all_posts(session)
            matching_posts = []
            for post in all_posts:
                # Check title and content (case-insensitive)
                title_match = post.title and query_lower in post.title.lower()
                content_match = query_lower in post.content.lower()
                
                if title_match or content_match:
                    author = _ops.get_user_by_id(session, post.user_id)
                    matching_posts.append({
                        "id": post.id,
                        "title": post.title,
                        "author_username": author.username if author else "unknown",
                        "created_at": post.created_at.isoformat()
                    })
            
            results["posts"] = matching_posts[:10]  # Limit to 10 results
        
        # Search users
        if search_type in ["all", "users"]:
            all_users = _ops.get_all_users(session)
            matching_users = []
            for user in all_users:
                # Check username (case-insensitive)
                if query_lower in user.username.lower():
                    matching_users.append({
                        "id": user.id,
                        "username": user.username,
                        "bio": user.bio
                    })
            
            results["users"] = matching_users[:10]  # Limit to 10 results
        
        # Search communities
        if search_type in ["all", "communities"]:
            all_communities = _ops.get_all_communities(session)
            matching_communities = []
            for community in all_communities:
                # Check name and description (case-insensitive)
                name_match = query_lower in community.name.lower()
                description_match = community.description and query_lower in community.description.lower()
                
                if name_match or description_match:
                    creator = _ops.get_user_by_id(session, community.created_by)
                    matching_communities.append({
                        "id": community.id,
                        "name": community.name,
                        "description": community.description,
                        "created_by": creator.username if creator else "unknown"
                    })
            
            results["communities"] = matching_communities[:10]  # Limit to 10 results
        
        # Count total results
        total_results = len(results["posts"]) + len(results["users"]) + len(results["communities"])
        
        return {
            "success": True,
            "message": f"Found {total_results} results for '{query}'",
            "data": {
                "query": query,
                "search_type": search_type,
                "results": results
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Search failed: {str(e)}",
            "data": None
        }

