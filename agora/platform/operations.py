"""
Atomic database operations.

Low-level CRUD operations that respect soft deletes and provide the foundation for higher-level social media tools
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

try:
    from .models import User, Post, Relationship, Reaction, Community, Membership, utc_now
except ImportError:
    from models import User, Post, Relationship, Reaction, Community, Membership, utc_now

class DatabaseOperationError(Exception):
    """Base exception for database operation errors"""
    pass

class UserNotFoundError(DatabaseOperationError):
    """Raised when a user cannot be found"""
    pass

class PostNotFoundError(DatabaseOperationError):
    """Raised when a post cannot be found"""
    pass

class DuplicateError(DatabaseOperationError):
    """Raised when attempting to create duplicate records"""
    pass

# =================================================================
# USER OPERATIONS
# =================================================================

def create_user(
    session: Session,
    username: str,
    bio: Optional[str] = None
) -> User:
    """
    Create a new user.
    
    Args:
        session: Database session
        username: Unique username
        bio: Optional user bio

    Returns:
        Created User object
    """
    user = User(
        username=username,
        bio=bio
    )

    try:
        session.add(user)
        session.flush()
        return user
    except IntegrityError as e:
        session.rollback()
        if "username" in str(e):
            raise DuplicateError(f"Username '{username}' already exists")
        else:
            raise DuplicateError(f"User creation failed: {e}")
        
def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
    """Get user by ID, excluding soft-deleted users."""
    return session.query(User).filter(
        and_(User.id == user_id, User.deleted_at.is_(None))
    ).first()

def get_user_by_username(session: Session, username: str) -> Optional[User]:
    """Get user by username, excluding soft-deleted users."""
    return session.query(User).filter(
        and_(User.username == username, User.deleted_at.is_(None))
    ).first()

def update_user(
    session: Session,
    user_id: int,
    **updates
) -> User:
    """
    Update user fields.
    
    Args:
        session: Database session
        user_id: User ID to update
        **updates: Fields to update (bio, etc.)
        
    Returns:
        Updated User object
        
    Raises:
        UserNotFoundError: If user doesn't exist
    """
    user = get_user_by_id(session, user_id)
    if not user:
        raise UserNotFoundError(f"User {user_id} not found")
    
    for field, value in updates.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    session.flush()
    return user

def soft_delete_user(session: Session, user_id: int) -> User:
    """Soft delete a user by setting deleted_at timestamp."""
    user = get_user_by_id(session, user_id)
    if not user:
        raise UserNotFoundError(f"User {user_id} not found")
    
    user.deleted_at = utc_now()
    session.flush()
    return user

# =================================================================
# POST OPERATIONS
# =================================================================

def create_post(
    session: Session,
    user_id: int,
    content: str,
    parent_post_id: Optional[int] = None,
    title: Optional[str] = None
) -> Post:
    """
    Create a new post or comment.
    
    Args:
        session: Database session
        user_id: ID of the user creating the post
        content: Post content
        parent_post_id: If provided, creates a comment on that post
        
    Returns:
        Created Post object
        
    Raises:
        UserNotFoundError: If user doesn't exist
        PostNotFoundError: If parent post doesn't exist
    """
    # Verify user exists
    if not get_user_by_id(session, user_id):
        raise UserNotFoundError(f"User {user_id} not found")
    
    # Verify parent post exists if this is a comment
    if parent_post_id and not get_post_by_id(session, parent_post_id):
        raise PostNotFoundError(f"Parent post {parent_post_id} not found")
    
    post = Post(
        user_id=user_id,
        content=content,
        parent_post_id=parent_post_id,
        title=title
    )
    
    session.add(post)
    session.flush()
    return post

def get_post_by_id(session: Session, post_id: int) -> Optional[Post]:
    """Get post by ID, excluding soft-deleted posts."""
    return session.query(Post).filter(
        and_(Post.id == post_id, Post.deleted_at.is_(None))
    ).first()

def get_post_by_title(session: Session, title: str) -> Optional[Post]:
    """Get post by title, excluding soft-deleted posts."""
    return session.query(Post).filter(
        and_(Post.title == title, Post.deleted_at.is_(None))
    ).first()

def get_posts_by_user(
    session: Session, 
    user_id: int, 
    limit: int = 50,
    include_comments: bool = False
) -> List[Post]:
    """
    Get posts by a user.
    
    Args:
        session: Database session
        user_id: User ID
        limit: Maximum number of posts to return
        include_comments: If True, include comments; if False, only top-level posts
        
    Returns:
        List of Post objects, newest first
    """
    query = session.query(Post).filter(
        and_(
            Post.user_id == user_id,
            Post.deleted_at.is_(None)
        )
    )
    
    if not include_comments:
        query = query.filter(Post.parent_post_id.is_(None))
    
    return query.order_by(desc(Post.created_at)).limit(limit).all()

def get_comments_for_post(session: Session, post_id: int) -> List[Post]:
    """Get all comments for a post, newest first."""
    return session.query(Post).filter(
        and_(
            Post.parent_post_id == post_id,
            Post.deleted_at.is_(None)
        )
    ).order_by(desc(Post.created_at)).all()

def soft_delete_post(session: Session, post_id: int) -> Post:
    """Soft delete a post by setting deleted_at timestamp."""
    post = get_post_by_id(session, post_id)
    if not post:
        raise PostNotFoundError(f"Post {post_id} not found")
    
    post.deleted_at = utc_now()
    session.flush()
    return post

# =================================================================
# RELATIONSHIP OPERATIONS
# =================================================================

def create_relationship(
    session: Session,
    follower_id: int,
    followed_id: int,
    relationship_type: str="follow"
) -> Relationship:
    """
    Create a relationship between users.
    
    Args:
        session: Database session
        follower_id: ID of the user creating the relationship
        followed_id: ID of the user being followed/friended
        relationship_type: Type of relationship ("follow", "friend", "block", etc.)
        
    Returns:
        Created Relationship object
        
    Raises:
        UserNotFoundError: If either user doesn't exist
        DuplicateError: If relationship already exists
    """
    # Verify both users exist
    if not get_user_by_id(session, follower_id):
        raise UserNotFoundError(f"User {follower_id} not found")
    if not get_user_by_id(session, followed_id):
        raise UserNotFoundError(f"User {followed_id} not found")
    
    # Check for existing relationship
    existing = get_relationship(session, follower_id, followed_id, relationship_type)
    if existing:
        raise DuplicateError(f"Relationship already exists: {follower_id} -> {followed_id} ({relationship_type})")
    
    relationship = Relationship(
        follower_id=follower_id,
        followed_id=followed_id,
        relationship_type=relationship_type
    )
    
    session.add(relationship)
    session.flush()
    return relationship

def get_relationship(
    session: Session,
    follower_id: int,
    followed_id: int,
    relationship_type: str = "follow"
) -> Optional[Relationship]:
    """Get specific relationship between two users."""
    return session.query(Relationship).filter(
        and_(
            Relationship.follower_id == follower_id,
            Relationship.followed_id == followed_id,
            Relationship.relationship_type == relationship_type,
            Relationship.deleted_at.is_(None)
        )
    ).first()

def get_followers(session: Session, user_id: int) -> List[User]:
    """Get all users following the specified user."""
    return session.query(User).join(
        Relationship, User.id == Relationship.follower_id
    ).filter(
        and_(
            Relationship.followed_id == user_id,
            Relationship.relationship_type == "follow",
            Relationship.deleted_at.is_(None),
            User.deleted_at.is_(None)
        )
    ).all()


def get_following(session: Session, user_id: int) -> List[User]:
    """Get all users that the specified user is following."""
    return session.query(User).join(
        Relationship, User.id == Relationship.followed_id
    ).filter(
        and_(
            Relationship.follower_id == user_id,
            Relationship.relationship_type == "follow",
            Relationship.deleted_at.is_(None),
            User.deleted_at.is_(None)
        )
    ).all()


def soft_delete_relationship(
    session: Session,
    follower_id: int,
    followed_id: int,
    relationship_type: str = "follow"
) -> Optional[Relationship]:
    """Soft delete a relationship (unfollow, unfriend, etc.)."""
    relationship = get_relationship(session, follower_id, followed_id, relationship_type)
    if relationship:
        relationship.deleted_at = utc_now()
        session.flush()
    return relationship

# =================================================================
# REACTION OPERATIONS
# =================================================================

def create_reaction(
    session: Session,
    user_id: int,
    post_id: int,
    reaction_type: str="like"
) -> Reaction:
    """
    Create or update a reaction to a post.
    
    Args:
        session: Database session
        user_id: ID of the user reacting
        post_id: ID of the post being reacted to
        reaction_type: Type of reaction ("like", "dislike", "love", etc.)
        
    Returns:
        Created or updated Reaction object
        
    Raises:
        UserNotFoundError: If user doesn't exist
        PostNotFoundError: If post doesn't exist
    """
    # Verify user and post exist
    if not get_user_by_id(session, user_id):
        raise UserNotFoundError(f"User {user_id} not found")
    if not get_post_by_id(session, post_id):
        raise PostNotFoundError(f"Post {post_id} not found")
    
    # Check for existing reaction
    existing = get_reaction(session, user_id, post_id, reaction_type)
    if existing:
        # Undelete if it was soft-deleted
        if existing.deleted_at:
            existing.deleted_at = None
            session.flush()
        return existing
    
    reaction = Reaction(
        user_id=user_id,
        post_id=post_id,
        reaction_type=reaction_type
    )
    
    session.add(reaction)
    session.flush()
    return reaction

def get_reaction(
    session: Session,
    user_id: int,
    post_id: int,
    reaction_type: str="like"
) -> Optional[Reaction]:
    """Get specific reaction from a user to a post"""
    return session.query(Reaction).filter(
        and_(
            Reaction.user_id == user_id,
            Reaction.post_id == post_id,
            Reaction.reaction_type == reaction_type,
            Reaction.deleted_at.is_(None)
        )
    ).first()

def get_post_reactions(
    session: Session,
    post_id: int,
    reaction_type: Optional[str] = None
) -> List[Reaction]:
    """Get all reactions for a post, optionally filtered by type."""
    query = session.query(Reaction).filter(
        and_(
            Reaction.post_id == post_id,
            Reaction.deleted_at.is_(None)
        )
    )
    
    if reaction_type:
        query = query.filter(Reaction.reaction_type == reaction_type)
    
    return query.all()


def get_reaction_counts(session: Session, post_id: int) -> Dict[str, int]:
    """Get reaction counts by type for a post."""
    results = session.query(
        Reaction.reaction_type,
        func.count(Reaction.id)
    ).filter(
        and_(
            Reaction.post_id == post_id,
            Reaction.deleted_at.is_(None)
        )
    ).group_by(Reaction.reaction_type).all()
    
    return {reaction_type: count for reaction_type, count in results}

def get_user_reactions(session: Session, user_id: int) -> List[Reaction]:
    """Get all reactions by a user (excluding soft-deleted ones)."""
    return session.query(Reaction).filter(
        and_(
            Reaction.user_id == user_id,
            Reaction.deleted_at.is_(None)
        )
    ).all()

def soft_delete_reaction(
    session: Session,
    user_id: int,
    post_id: int,
    reaction_type: str = "like"
) -> Optional[Reaction]:
    """Soft delete a reaction (remove like, etc.)."""
    reaction = get_reaction(session, user_id, post_id, reaction_type)
    if reaction:
        reaction.deleted_at = utc_now()
        session.flush()
    return reaction

# =================================================================
# COMMUNITY OPERATIONS
# =================================================================

def create_community(
    session: Session,
    name: str,
    created_by: int,
    description: Optional[str] = None
) -> Community:
    """
    Create a new community.
    
    Args:
        session: Database session
        name: Unique community name
        created_by: ID of the user creating the community
        description: Optional community description
        
    Returns:
        Created Community object
        
    Raises:
        UserNotFoundError: If creator doesn't exist
        DuplicateError: If community name already exists
    """
    # Verify creator exists
    if not get_user_by_id(session, created_by):
        raise UserNotFoundError(f"User {created_by} not found")
    
    community = Community(
        name=name,
        created_by=created_by,
        description=description
    )
    
    try:
        session.add(community)
        session.flush()
        return community
    except IntegrityError:
        session.rollback()
        raise DuplicateError(f"Community name '{name}' already exists")
    
def get_community_by_id(session: Session, community_id: int) -> Optional[Community]:
    """Get community by ID, excluding soft-deleted communities."""
    return session.query(Community).filter(
        and_(Community.id == community_id, Community.deleted_at.is_(None))
    ).first()


def get_community_by_name(session: Session, name: str) -> Optional[Community]:
    """Get community by name, excluding soft-deleted communities."""
    return session.query(Community).filter(
        and_(Community.name == name, Community.deleted_at.is_(None))
    ).first()

# =================================================================
# MEMBERSHIP OPERATIONS
# =================================================================

def create_membership(
    session: Session,
    user_id: int,
    community_id: int,
    role: str="member"
) -> Membership:
    """
    Create a community membership.
    
    Args:
        session: Database session
        user_id: ID of the user joining
        community_id: ID of the community
        role: User role in the community
        
    Returns:
        Created Membership object
        
    Raises:
        UserNotFoundError: If user doesn't exist
        DatabaseOperationError: If community doesn't exist
        DuplicateError: If membership already exists
    """
    # Verify user and community exist
    if not get_user_by_id(session, user_id):
        raise UserNotFoundError(f"User {user_id} not found")
    if not get_community_by_id(session, community_id):
        raise DatabaseOperationError(f"Community {community_id} not found")
    
    # Check for existing membership
    existing = get_membership(session, user_id, community_id)
    if existing:
        raise DuplicateError(f"User {user_id} already member of community {community_id}")
    
    membership = Membership(
        user_id=user_id,
        community_id=community_id,
        role=role
    )
    
    session.add(membership)
    session.flush()
    return membership

def get_membership(
    session: Session,
    user_id: int,
    community_id: int
) -> Optional[Membership]:
    """Get specific membership."""
    return session.query(Membership).filter(
        and_(
            Membership.user_id == user_id,
            Membership.community_id == community_id,
            Membership.deleted_at.is_(None)
        )
    ).first()


def get_user_communities(session: Session, user_id: int) -> List[Community]:
    """Get all communities a user is a member of."""
    return session.query(Community).join(
        Membership, Community.id == Membership.community_id
    ).filter(
        and_(
            Membership.user_id == user_id,
            Membership.deleted_at.is_(None),
            Community.deleted_at.is_(None)
        )
    ).all()


def get_community_members(session: Session, community_id: int) -> List[User]:
    """Get all members of a community."""
    return session.query(User).join(
        Membership, User.id == Membership.user_id
    ).filter(
        and_(
            Membership.community_id == community_id,
            Membership.deleted_at.is_(None),
            User.deleted_at.is_(None)
        )
    ).all()