"""
Synthetic Agora Platform Layer

Provides the foundational data model and operations for social media simulation.

This module exposes a clean API for platform operations while hiding internal complexity.
"""

from .connection import DatabaseManager, initialize_database
from . import services

# Expose connection management
__all__ = [
    'DatabaseManager',
    'initialize_database', 
    'services'
]