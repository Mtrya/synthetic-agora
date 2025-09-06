"""
Pytest configuration and fixtures for Synthetic Agora tests.
"""

import pytest
import tempfile
import os
from agora.platform import DatabaseManager, initialize_database, services
from agora.runtime import AgentToolExecutor


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        # Initialize database
        db_manager = initialize_database(db_path)
        yield db_manager
    finally:
        # Cleanup
        db_manager.close()
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture
def tool_executor(temp_db):
    """Create a tool executor with temporary database."""
    return AgentToolExecutor(temp_db)


@pytest.fixture
def sample_users(temp_db):
    """Create sample users for testing."""
    with temp_db.get_session() as session:
        # Create test users
        services.create_user_account(session, "alice", "AI researcher")
        services.create_user_account(session, "bob", "Developer")
        services.create_user_account(session, "charlie", "Designer")
    
    return ["alice", "bob", "charlie"]