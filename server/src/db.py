import logging
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy import create_engine
from typing import Generator
from models import Base

# Setup logging
logger = logging.getLogger(__name__)

# Get database URL from environment variable or use a default SQLite database
DATABASE_URL = "sqlite:///../autolabel.db"
engine = create_engine(DATABASE_URL, echo=False)

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
