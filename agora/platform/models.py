"""
Database models for Synthetic Agora social media simulation.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    UniqueConstraint, Index, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

def utc_now() -> datetime:
    """Return current UTC timestamp"""
    return datetime.now(timezone.utc)

class User(Base):
    """User profiles and account information"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=True, index=True)
    bio = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True),nullable=False,default=utc_now)
    deleted_at = Column(DateTime(timezone=True),nullable=True) # soft delete

    # Following relationships
    following = relationship(
        "Relationship",
        foreign_keys="Relationship.follower_id",
        back_populates="follower"
    )
    followers = relationship(
        "Relationship",
        foreign_keys="Relationship.followed_id",
        back_populates="followed"
    )

    # Community relationships
    memberships = relationship("Membership", back_populates="user")
    created_communities = relationship("Community", back_populates="creator")
    
    # Post relationships
    posts = relationship("Post", back_populates="author")
    reactions = relationship("Reaction", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"
    
class Post(Base):
    """Posts and comments (comments have parent_post_id)"""
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    parent_post_id = Column(Integer, ForeignKey('posts.id'), nullable=True, index=True)
    title = Column(String(200), nullable=True, index=True)
    content = Column(Text, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True),nullable=False, default=utc_now)
    deleted_at = Column(DateTime(timezone=True),nullable=True) # soft delete

    # Relationships
    author = relationship("User", back_populates="posts")
    parent_post = relationship("Post", remote_side=[id], backref="comments")
    reactions = relationship("Reaction", back_populates="post")

    def __repr__(self):
        post_type = "Comment" if self.parent_post_id else "Post"
        return f"<{post_type}(id={self.id}, user_id={self.user_id})>"
    
    @property
    def is_comment(self) -> bool:
        """True if this post is a comment (has parent_post_id)"""
        return self.parent_post_id is not None
    
class Relationship(Base):
    """User-to-user relationships (follow, friend, etc.)"""
    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    followed_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    relationship_type = Column(String(20), nullable=False, default="follow") # follow, friend, block, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete

    # Relationships
    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")
    followed = relationship("User", foreign_keys=[followed_id], back_populates="followers")

    # Constraints
    __table_args__ = (
        UniqueConstraint('follower_id', 'followed_id', 'relationship_type', name='unique_relationship'),
        Index('idx_follower_followed', 'follower_id', 'followed_id')
    )

    def __repr__(self):
        return f"<Relationship(follower={self.follower_id}, followed={self.followed_id}, type='{self.relationship_type}')>"
    
class Reaction(Base):
    """Reactions to posts (like, dislike, love, etc.)"""
    __tablename__ = "reactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False, index=True)
    reaction_type = Column(String(20), nullable=False, default="like") # like, dislike, love, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    
    # Relationships
    user = relationship("User", back_populates="reactions")
    post = relationship("Post", back_populates="reactions")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'post_id', 'reaction_type', name='unique_reaction'),
        Index('idx_user_post', 'user_id', 'post_id'),
    )
    
    def __repr__(self):
        return f"<Reaction(user={self.user_id}, post={self.post_id}, type='{self.reaction_type}')>"
    
class Community(Base):
    """Communities/Groups for organizing users."""
    __tablename__ = "communities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    
    # Relationships
    creator = relationship("User", back_populates="created_communities")
    memberships = relationship("Membership", back_populates="community")
    
    def __repr__(self):
        return f"<Community(id={self.id}, name='{self.name}')>"
    
class Membership(Base):
    """User memberships in communities."""
    __tablename__ = 'memberships'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    community_id = Column(Integer, ForeignKey('communities.id'), nullable=False, index=True)
    role = Column(String(20), nullable=False, default='member')  # member, admin, moderator
    
    # Timestamps
    joined_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    
    # Relationships
    user = relationship("User", back_populates="memberships")
    community = relationship("Community", back_populates="memberships")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'community_id', name='unique_membership'),
        Index('idx_user_community', 'user_id', 'community_id'),
    )
    
    def __repr__(self):
        return f"<Membership(user={self.user_id}, community={self.community_id}, role='{self.role}')>"
    
# Utility functions for database setup
def create_database_engine(database_url: str="sqlite:///synthetic_agora.db"):
    """Create SQLAlchemy engine with proper SQLite configuration"""
    engine = create_engine(
        database_url,
        echo=False,
        connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {}
    )
    return engine

def create_tables(engine):
    """Create all tables in the database"""
    Base.metadata.create_all(engine)

def create_session_factory(engine):
    """Create a session factory bound to the engine"""
    return sessionmaker(bind=engine)

if __name__ == "__main__":
    # Quick test
    engine = create_database_engine()
    create_tables(engine)

    print("Database tables created successfully")

    print("\nCreated tables:")
    for table_name in Base.metadata.tables.keys():
        print(f"    - {table_name}")