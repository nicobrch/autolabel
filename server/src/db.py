import logging
import os
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from typing import Generator
from src.models import Base


# Enable foreign key constraints for SQLite so ON DELETE CASCADE works
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


# Setup logging
logger = logging.getLogger(__name__)

# Define the data directory within the /app directory
DATA_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

# Get database URL from environment variable or use a default SQLite database
DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'autolabel.db')}"
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a scoped session factory
session_factory = sessionmaker(bind=engine)
SessionLocal = scoped_session(session_factory)


# Create tables
def create_tables() -> None:
    """Create all tables defined in models."""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


# Get DB session
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database when script is run directly
if __name__ == "__main__":
    # Configure logging for direct script execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    create_tables()
