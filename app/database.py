"""
Database initialization and session management using SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative class definitions
Base = declarative_base()

def init_db():
    """
    Initialize database tables.
    """
    # Import models so they are registered on the metadata
    from app.models import task  # noqa: F401
    Base.metadata.create_all(bind=engine)

def close_db():
    """
    Close database connection/dispose engine.
    """
    engine.dispose()