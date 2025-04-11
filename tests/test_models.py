import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from app.models import Base, User, Persona, LinkedInAccount, Post, PostAnalytics, PostStatus, PostTone

# Setup in-memory SQLite database for testing
@pytest.fixture
def db_engine():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()

# Test User model
def test_user_creation(db_session):
    # Create a test user
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    
    # Query the user
    queried_user = db_session.query(User).filter(User.email == "test@example.com").first()
    
    # Verify user attributes
    assert queried_user is not None
    assert queried_user.email == "test@example.com"
    assert queried_user.username == "testuser"
    assert queried_user.hashed_password == "hashed_password"
    assert queried_user.full_name == "Test User"
    assert queried_user.is_active == True
    assert queried_user.created_at is not None
    assert queried_user.updated_at is not None

# Test Persona model
def test_persona_creation(db_session):
    # Create a test user first
    user = User(email="test@example.com", username="testuser", hashed_password="hashed_password")
    db_session.add(user)
    db_session.commit()
    
    # Create a persona for the user
    persona = Persona(
        user_id=user.id,
        name="Tech Expert",
        description="A technology industry expert with 10+ years experience"
    )
    db_session.add(persona)
    db_session.commit()
    
    # Query the persona
    queried_persona = db_session.query(Persona).filter(Persona.name == "Tech Expert").first()
    
    # Verify persona attributes
    assert queried_persona is not None
    assert queried_persona.user_id == user.id
    assert queried_persona.name == "Tech Expert"
    assert queried_persona.description == "A technology industry expert with 10+ years experience"
    assert queried_persona.created_at is not None
    assert queried_persona.updated_at is not None
    
    # Verify relationship with user
    assert queried_persona.user.id == user.id
    assert queried_persona.user.email == "test@example.com"

# Test LinkedInAccount model
def test_linkedin_account_creation(db_session):
    # Create a test user first
    user = User(email="test@example.com", username="testuser", hashed_password="hashed_password")
    db_session.add(user)
    db_session.commit()
    
    # Create a LinkedIn account for the user
    expires_at = datetime.now() + timedelta(days=60)
    linkedin_account = LinkedInAccount(
        user_id=user.id,
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        token_expires_at=expires_at,
        profile_id="test_profile_id",
        profile_url="https://linkedin.com/in/testprofile"
    )
    db_session.add(linkedin_account)
    db_session.commit()
    
    # Query the LinkedIn account
    queried_account = db_session.query(LinkedInAccount).filter(
        LinkedInAccount.profile_id == "test_profile_id"
    ).first()
    
    # Verify LinkedIn account attributes
    assert queried_account is not None
    assert queried_account.user_id == user.id
    assert queried_account.access_token == "test_access_token"
    assert queried_account.refresh_token == "test_refresh_token"
    assert queried_account.token_expires_at == expires_at
    assert queried_account.profile_id == "test_profile_id"
    assert queried_account.profile_url == "https://linkedin.com/in/testprofile"
    assert queried_account.created_at is not None
    assert queried_account.updated_at is not None
    
    # Verify relationship with user
    assert queried_account.user.id == user.id

# Test Post model
def test_post_creation(db_session):
    # Create a test user first
    user = User(email="test@example.com", username="testuser", hashed_password="hashed_password")
    db_session.add(user)
    
    # Create a persona
    persona = Persona(user_id=user.id, name="Tech Expert", description="A technology expert")
    db_session.add(persona)
    
    # Create a LinkedIn account
    linkedin_account = LinkedInAccount(
        user_id=user.id,
        access_token="test_access_token",
        profile_id="test_profile_id",
        profile_url="https://linkedin.com/in/testprofile"
    )
    db_session.add(linkedin_account)
    db_session.commit()
    
    # Create a post
    scheduled_time = datetime.now() + timedelta(days=1)
    post = Post(
        user_id=user.id,
        persona_id=persona.id,
        linkedin_account_id=linkedin_account.id,
        content="This is a test LinkedIn post about technology trends.",
        tone=PostTone.PROFESSIONAL,
        status=PostStatus.SCHEDULED,
        scheduled_time=scheduled_time,
        source_type="text",
        source_data={"text": "Original text for the post"}
    )
    db_session.add(post)
    db_session.commit()
    
    # Query the post
    queried_post = db_session.query(Post).filter(Post.user_id == user.id).first()
    
    # Verify post attributes
    assert queried_post is not None
    assert queried_post.user_id == user.id
    assert queried_post.persona_id == persona.id
    assert queried_post.linkedin_account_id == linkedin_account.id
    assert queried_post.content == "This is a test LinkedIn post about technology trends."
    assert queried_post.tone == PostTone.PROFESSIONAL
    assert queried_post.status == PostStatus.SCHEDULED
    assert queried_post.scheduled_time == scheduled_time
    assert queried_post.source_type == "text"
    assert queried_post.source_data == {"text": "Original text for the post"}
    assert queried_post.created_at is not None
    assert queried_post.updated_at is not None
    
    # Verify relationships
    assert queried_post.author.id == user.id
    assert queried_post.persona.id == persona.id
    assert queried_post.linkedin_account.id == linkedin_account.id

# Test PostAnalytics model
def test_post_analytics_creation(db_session):
    # Create a test user
    user = User(email="test@example.com", username="testuser", hashed_password="hashed_password")
    db_session.add(user)
    
    # Create a post
    post = Post(
        user_id=user.id,
        content="Test post content",
        tone=PostTone.PROFESSIONAL,
        status=PostStatus.PUBLISHED,
        published_time=datetime.now(),
        linkedin_post_id="test_linkedin_post_id"
    )
    db_session.add(post)
    db_session.commit()
    
    # Create post analytics
    analytics = PostAnalytics(
        post_id=post.id,
        impressions=1000,
        likes=50,
        comments=10,
        shares=5,
        clicks=100
    )
    db_session.add(analytics)
    db_session.commit()
    
    # Query the analytics
    queried_analytics = db_session.query(PostAnalytics).filter(PostAnalytics.post_id == post.id).first()
    
    # Verify analytics attributes
    assert queried_analytics is not None
    assert queried_analytics.post_id == post.id
    assert queried_analytics.impressions == 1000
    assert queried_analytics.likes == 50
    assert queried_analytics.comments == 10
    assert queried_analytics.shares == 5
    assert queried_analytics.clicks == 100
    
    # Verify relationship with post
    assert queried_analytics.post.id == post.id
    assert queried_analytics.post.content == "Test post content"

# Test cascade delete
def test_cascade_delete(db_session):
    # Create a test user
    user = User(email="test@example.com", username="testuser", hashed_password="hashed_password")
    db_session.add(user)
    
    # Create a persona
    persona = Persona(user_id=user.id, name="Tech Expert", description="A technology expert")
    db_session.add(persona)
    
    # Create a post
    post = Post(
        user_id=user.id,
        persona_id=persona.id,
        content="Test post content",
        tone=PostTone.PROFESSIONAL,
        status=PostStatus.PUBLISHED
    )
    db_session.add(post)
    
    # Create post analytics
    analytics = PostAnalytics(
        post_id=post.id,
        impressions=1000,
        likes=50
    )
    db_session.add(analytics)
    db_session.commit()
    
    # Delete the post and verify analytics is also deleted
    db_session.delete(post)
    db_session.commit()
    
    # Verify analytics is deleted
    queried_analytics = db_session.query(PostAnalytics).filter(PostAnalytics.post_id == post.id).first()
    assert queried_analytics is None
    
    # Verify persona still exists
    queried_persona = db_session.query(Persona).filter(Persona.id == persona.id).first()
    assert queried_persona is not None