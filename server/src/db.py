from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import os

# Get database URL from environment variable or use a default SQLite database
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///../autolabel.db")
engine = create_engine(DATABASE_URL, echo=False)

# Create a scoped session factory
session_factory = sessionmaker(bind=engine)
SessionLocal = scoped_session(session_factory)

# Create declarative base
Base = declarative_base()


# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)


# Get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database
if __name__ == "__main__":
    create_tables()
    print("Database tables created.")
