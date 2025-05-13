from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base, Session
from typing import Generator
import os
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Get database URL from environment variable or use a default SQLite database
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///../autolabel.db")
engine = create_engine(DATABASE_URL, echo=False)

# Create a scoped session factory
session_factory = sessionmaker(bind=engine)
SessionLocal = scoped_session(session_factory)

# Create declarative base
Base = declarative_base()


# Create tables
def create_tables() -> None:
    """Create all tables defined in models."""
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        if not existing_tables:
            logger.info("Creating database tables...")
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully.")
        else:
            logger.info(
                f"Database already contains tables: {', '.join(existing_tables)}")

            # Check for any new tables that need to be created
            model_tables = [
                table.name for table in Base.metadata.sorted_tables]
            missing_tables = set(model_tables) - set(existing_tables)

            if missing_tables:
                logger.info(
                    f"Creating missing tables: {', '.join(missing_tables)}")
                Base.metadata.create_all(bind=engine)
                logger.info("Missing tables created successfully.")

    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def init_db() -> None:
    """Initialize the database with all required tables and default data."""
    create_tables()

    # Here you could also add code to populate default/seed data if needed
    # Example:
    # session = SessionLocal()
    # try:
    #     if session.query(SomeModel).count() == 0:
    #         session.add(SomeModel(...))
    #         session.commit()
    # finally:
    #     session.close()

    logger.info("Database initialization complete.")


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
    init_db()
