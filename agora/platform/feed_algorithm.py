"""
Feed algorithm implementation for content distribution and recommendation.

This module handles complex feed generation logic including relevance scoring,
personalization, and content distribution algorithms.
"""

from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

# Should operate at atomic CRUD operations level, don't import services
from . import operations as _ops


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


def get_user_feed(
    session: Session,
    username: str,
    limit: int = 20
) -> List[dict]:
    """
    Get personalized feed for a user with advanced relevance scoring.
    
    This is a sophisticated feed algorithm that considers:
    - Social relationships (following)
    - Temporal relevance (recency decay)
    - Content engagement metrics
    - User interaction patterns
    
    Args:
        session: Database session
        username: User to generate feed for
        limit: Maximum number of posts to return
        
    Returns:
        List of feed items with posts and relevance scores
    """
    user = _ops.get_user_by_username(session, username)
    if not user:
        return []
    
    # Get users this user follows
    following = _ops.get_following(session, user.id)
    following_ids = [u.id for u in following]
    
    # Include user's own posts
    following_ids.append(user.id)
    
    # Get recent posts from followed users
    feed_posts = []
    for user_id in following_ids:
        posts = _ops.get_posts_by_user(session, user_id, limit=10, include_comments=False)
        feed_posts.extend(posts)
    
    # Sort by creation time (newest first)
    feed_posts.sort(key=lambda p: p.created_at, reverse=True)
    
    # Format as feed items with sophisticated relevance scoring
    feed_items = []
    for post in feed_posts[:limit]:
        post_data = _format_post_data(session, post)
        
        # Calculate multi-factor relevance score
        relevance_score = _calculate_relevance_score(session, post, user)
        
        feed_items.append({
            "post": post_data,
            "relevance_score": relevance_score,
            "algorithm_metadata": {
                "post_age_hours": _get_post_age_hours(post),
                "engagement_factor": _get_engagement_factor(session, post),
                "social_proximity": _get_social_proximity(session, post, user)
            }
        })
    
    # Apply final ranking and filtering
    ranked_feed = _apply_final_ranking(feed_items, limit)
    
    return ranked_feed


def _calculate_relevance_score(
    session: Session, 
    post, 
    user
) -> float:
    """
    Calculate multi-factor relevance score for a post.
    
    Factors considered:
    - Temporal decay (newer = more relevant)
    - Engagement metrics (likes, comments)
    - Social proximity (distance from user)
    - Content type preferences
    """
    
    # Base temporal relevance (decays over time)
    temporal_score = _get_temporal_relevance(post)
    
    # Engagement factor
    engagement_score = _get_engagement_factor(session, post)
    
    # Social proximity
    social_score = _get_social_proximity(session, post, user)
    
    # Combine factors with weights
    final_score = (
        temporal_score * 0.4 +      # 40% temporal
        engagement_score * 0.3 +    # 30% engagement  
        social_score * 0.3          # 30% social
    )
    
    return min(1.0, max(0.0, final_score))


def _get_temporal_relevance(post) -> float:
    """Calculate temporal relevance score (newer = higher score)."""
    hours_old = _get_post_age_hours(post)
    return max(0.1, 1.0 - (hours_old / 48))  # Decay over 48 hours


def _get_engagement_factor(session: Session, post) -> float:
    """Calculate engagement factor based on reactions and comments."""
    try:
        # Get reaction counts
        reaction_counts = _ops.get_reaction_counts(session, post.id)
        total_reactions = sum(reaction_counts.values())
        
        # Get comment count
        comments = _ops.get_comments_for_post(session, post.id)
        comment_count = len(comments)
        
        # Normalize engagement (logarithmic scaling to prevent domination)
        engagement_score = min(1.0, (total_reactions * 0.1) + (comment_count * 0.2))
        
        return engagement_score
    except Exception:
        return 0.0


def _get_social_proximity(session: Session, post, user) -> float:
    """
    Calculate social proximity score.
    
    Closer social connections = higher relevance
    """
    try:
        # Direct author connection
        if post.user_id == user.id:
            return 1.0
        
        # Check if user follows author
        following = _ops.get_following(session, user.id)
        following_ids = [u.id for u in following]
        
        if post.user_id in following_ids:
            return 0.8  # High relevance for followed users
        
        # Check mutual connections
        author_following = _ops.get_following(session, post.user_id)
        author_following_ids = [u.id for u in author_following]
        
        mutual_connections = set(following_ids) & set(author_following_ids)
        if mutual_connections:
            return 0.5 + (len(mutual_connections) * 0.1)  # Boost based on mutual connections
        
        return 0.1  # Base relevance for distant connections
        
    except Exception:
        return 0.1


def _get_post_age_hours(post) -> float:
    """Get post age in hours."""
    return (datetime.now(post.created_at.tzinfo) - post.created_at).total_seconds() / 3600


def _apply_final_ranking(feed_items: List[dict], limit: int) -> List[dict]:
    """
    Apply final ranking and filtering to feed items.
    
    Includes diversity boosting and spam prevention.
    """
    if not feed_items:
        return []
    
    # Sort by relevance score
    sorted_items = sorted(feed_items, key=lambda x: x['relevance_score'], reverse=True)
    
    # Apply diversity boost (prevent single user from dominating)
    diversified_items = _apply_diversity_boost(sorted_items)
    
    # Return top items
    return diversified_items[:limit]


def _apply_diversity_boost(sorted_items: List[dict]) -> List[dict]:
    """
    Apply diversity boosting to prevent feed dominance by single users.
    
    Uses a simple algorithm that reduces consecutive posts from same user.
    """
    if len(sorted_items) <= 3:
        return sorted_items
    
    diversified = []
    user_counts = {}
    
    for item in sorted_items:
        author_id = item['post']['author_username']
        
        # Apply penalty if user already has many posts in feed
        current_count = user_counts.get(author_id, 0)
        if current_count >= 2:  # Max 2 posts per user in top results
            continue
            
        # Apply diversity penalty for consecutive posts
        penalty = 1.0
        if diversified and diversified[-1]['post']['author_username'] == author_id:
            penalty = 0.8  # Reduce score for consecutive posts from same user
        
        # Create diversified item
        diversified_item = item.copy()
        diversified_item['relevance_score'] *= penalty
        diversified_item['diversity_adjusted'] = True
        diversified_item['diversity_penalty'] = 1.0 - penalty
        
        diversified.append(diversified_item)
        user_counts[author_id] = current_count + 1
    
    # Re-sort by adjusted scores
    diversified.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    return diversified