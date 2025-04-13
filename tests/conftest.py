import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base

@pytest.fixture
def db_session():
    # Create an in-memory SQLite database for testing
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool
    )
    
    # Import all models to ensure they are registered with Base metadata
    from app.models import User, Persona, LinkedInAccount, Post, PostAnalytics
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create a new session factory bound to the engine
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create a new session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        # Clean up after the test
        session.close()
        Base.metadata.drop_all(engine)