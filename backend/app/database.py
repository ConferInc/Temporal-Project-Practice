"""
Production-Grade Database Connection Layer

This module provides the database connection infrastructure using SQLModel.
It wraps the core database module and exposes utilities for use by both
FastAPI routes and Temporal activities.
"""
import os
from typing import Generator
from contextlib import contextmanager

from sqlmodel import SQLModel, create_engine, Session

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:temporal@postgres:5432/temporal"
)

# Create engine with production-ready settings
# - pool_pre_ping: Verify connections before use (handles stale connections)
# - pool_size: Number of connections to maintain
# - max_overflow: Additional connections allowed beyond pool_size
# - echo: Set to False in production to reduce log noise
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)


def init_db() -> None:
    """
    Initialize the database by creating all tables defined in SQLModel metadata.

    This should be called once at application startup or via the init_db.py script.
    """
    # Import all models to ensure they're registered with SQLModel
    from app.models.sql import User, Application, LoanStage
    from app.models.application import LoanApplication

    SQLModel.metadata.create_all(engine)
    print("Database tables created successfully.")


def get_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.

    Usage in FastAPI routes:
        @router.get("/items")
        def get_items(session: Session = Depends(get_session)):
            ...
    """
    with Session(engine) as session:
        yield session


@contextmanager
def get_session_context():
    """
    Context manager for database sessions, useful in Temporal activities
    or non-FastAPI code where Depends() isn't available.

    Usage:
        with get_session_context() as session:
            session.add(item)
            session.commit()
    """
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


def get_sync_session() -> Session:
    """
    Get a synchronous session directly (caller is responsible for closing).

    Use get_session_context() when possible for automatic cleanup.
    """
    return Session(engine)
