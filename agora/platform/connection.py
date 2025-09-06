"""
Database connection management.
Handles SQLite database setup, connection pooling, and session management
with support for batch operations and checkpointing
"""

import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

try:
    from .models import Base
except ImportError:
    from models import Base

class DatabaseManager:
    """Centralized database connection and session management"""

    def __init__(
        self,
        database_path: str="synthetic_agora.db",
        echo: bool=False
    ):
        """Initialize database manager"""
        self.database_path = Path(database_path)
        self.echo = echo
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine
    
    @property
    def session_factory(self) -> sessionmaker:
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self.engine)
        return self._session_factory
    
    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine with SQLite optimizations"""
        database_url = f"sqlite:///{self.database_path}"

        engine = create_engine(
            database_url,
            echo=self.echo,
            # SQLite optimizations for concurrent access
            poolclass=StaticPool,
            connect_args={
                "check_same_thread": False,
                "timeout": 30,
            },
            pool_pre_ping=True,
            pool_recycle=3600
        )

        # Register SQLite optimization pragmas
        self._configure_sqlite_pragmas(engine)

        return engine
    
    def _configure_sqlite_pragmas(self, engine: Engine) -> None:
        """Configure SQLite PRAGMA settings for performance"""

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            if isinstance(dbapi_connection, sqlite3.Connection):
                cursor = dbapi_connection.cursor()
                # Performance optimizations
                cursor.execute("PRAGMA journal_mode=WAL")      # Write-Ahead Logging for concurrency
                cursor.execute("PRAGMA synchronous=NORMAL")    # Faster writes, still safe
                cursor.execute("PRAGMA cache_size=10000")      # 10MB cache
                cursor.execute("PRAGMA temp_store=MEMORY")     # Temp tables in memory
                cursor.execute("PRAGMA mmap_size=268435456")   # 256MB memory-mapped I/O
                # Foreign key enforcement
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    def initialize_database(self) -> None:
        """Create all tables and indexes."""
        Base.metadata.create_all(self.engine)
        print(f"Database initialized: {self.database_path}")

    def reset_database(self) -> None:
        """Drop and recreate all tables. WARNING: Destroys all data!"""
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engines)
        print(f"Database reset: {self.database_path}")

    @contextmanager
    def get_session(self, autocommit: bool=True):
        """
        Context manager for database sessions
        
        Usage:
            with db_manager.get_session() as session:
                user = User(username="test)
                session.add(user)
                # Auto-commits on exit
        """
        session = self.session_factory()
        try:
            yield session
            if autocommit:
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def batch_operation(self):
        """
        Context manager for batch operations with explicit transaction control.
        Multiple operations must succeed or fail together.

        Usage:
            with db_manager.batch_operations() as session:
                # Multiple operations here
                session.bulk_insert_mappings(Post, posts_data)
                session.bulk_update_mappings(User, users_data)
                # Commits only if all operations succeeed
        """
        session = self.session_factory()
        transaction = session.begin()
        try:
            yield session
            transaction.commit()
        except Exception:
            transaction.rollback()
            raise
        finally:
            session.close()

    def create_checkpoint(self, checkpoint_name: Optional[str]=None) -> str:
        """Create a checkpoint (backup copy) of the database"""
        if checkpoint_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            checkpoint_name = f"checkpoint_{timestamp}"
        
        checkpoint_path = self.database_path.parent / f"{checkpoint_name}.db"
        
        # Use SQLite backup API for consistent snapshots
        with sqlite3.connect(str(self.database_path)) as source:
            with sqlite3.connect(str(checkpoint_path)) as backup:
                source.backup(backup)
        
        print(f"Checkpoint created: {checkpoint_path}")
        return str(checkpoint_path)
    
    def restore_checkpoint(self, checkpoint_path: str) -> None:
        """
        Restore database from checkpoint.
        
        Args:
            checkpoint_path: Path to checkpoint file
        """
        checkpoint_file = Path(checkpoint_path)
        if not checkpoint_file.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
        
        # Close existing connections
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
        
        # Replace database file
        shutil.copy2(checkpoint_file, self.database_path)
        print(f"Database restored from: {checkpoint_path}")

    def get_database_info(self) -> Dict[str, Any]:
        """Get database statistics and information."""
        with self.get_session() as session:
            info = {
                "database_path": str(self.database_path),
                "database_size_mb": self.database_path.stat().st_size / (1024 * 1024),
                "table_counts": {}
            }
            
            # Get row counts for each table
            for table_name, table in Base.metadata.tables.items():
                count = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                info["table_counts"][table_name] = count
            
            return info
    
    def close(self) -> None:
        """Close database connections and clean up resources."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
        print("Database connections closed")

# Global database manager instance
_db_manager: Optional[DatabaseManager] = None

def get_database_manager(
        database_path: str="synthetic_agora.db",
        echo: bool=False
) -> DatabaseManager:
    global _db_manager
    if _db_manager is None or _db_manager.database_path != Path(database_path):
        _db_manager = DatabaseManager(database_path, echo)
    return _db_manager

def initialize_database(database_path: str="synthetic_agora.db") -> DatabaseManager:
    """Initialize database with all tables"""
    db_manager = get_database_manager(database_path)
    db_manager.initialize_database()
    return db_manager


if __name__ == "__main__":
    # Demo/test the connection manager
    print("Testing DatabaseManager...")
    
    # Initialize database
    db = initialize_database("test_synthetic_agora.db")
    
    # Show database info
    info = db.get_database_info()
    print(f"\nDatabase Info:")
    print(f"  Path: {info['database_path']}")
    print(f"  Size: {info['database_size_mb']:.2f} MB")
    print(f"  Tables: {list(info['table_counts'].keys())}")
    
    # Test checkpoint
    checkpoint_file = db.create_checkpoint("test_checkpoint")
    
    # Clean up
    db.close()
    Path("test_synthetic_agora.db").unlink(missing_ok=True)
    Path(checkpoint_file).unlink(missing_ok=True)
    
    print("DatabaseManager test completed!")

