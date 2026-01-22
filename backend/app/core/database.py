from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from app.core import config

# echo=True is good for debugging SQL queries during development
engine = create_engine(config.DATABASE_URL, echo=True)

def init_db():
    """Creates the database tables based on the SQLModel metadata."""
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """Dependency that provides a database session."""
    with Session(engine) as session:
        yield session
