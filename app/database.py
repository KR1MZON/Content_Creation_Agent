from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get database URL from environment variables or use a default SQLite URL for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./linkedin_automation.db")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database (create tables)
def init_db():
    # Import all models here to ensure they are registered with the Base metadata
    from app.models import User, Persona, LinkedInAccount, Post, PostAnalytics
    
    # Create tables
    Base.metadata.create_all(bind=engine)