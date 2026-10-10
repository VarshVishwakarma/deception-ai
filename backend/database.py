import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# --- Configuration ---
# Creates a local SQLite database file named 'deception_ai.db' in the root directory.
SQLALCHEMY_DATABASE_URL = "sqlite:///./deception_ai.db"

# --- Engine Setup ---
# The engine is the starting point for any SQLAlchemy application.
# `check_same_thread=False` is specifically required for SQLite in FastAPI 
# because FastAPI can process multiple requests on different threads.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# --- Session Factory ---
# Each instance of the SessionLocal class will be a distinct database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Base Model ---
# We will inherit from this Base class to create our database models (tables) later.
Base = declarative_base()

# --- Dependency ---
def get_db():
    """
    FastAPI dependency that yields a database session for a single API request.
    Using 'yield' ensures the database connection is safely closed after the 
    API responds, even if an error occurs during the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()