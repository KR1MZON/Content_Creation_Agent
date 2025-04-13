import pytest
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, Post, PostStatus, PostTone, LinkedInAccount, Persona
from app.routers.scheduler import router
from app.auth import get_current_active_user

# Mock authenticated user for testing
async def override_get_current_active_user():
    return User(id=1, email="test@example.com", username="testuser", hashed_password="hashed_password")

# Create test app
app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_current_active_user] = override_get_current_active_user

# Test client
client = TestClient(app)

@pytest.fixture
def test_user(db_session):
    # Create a test user
    user = User(email="test@example.com", username="testuser", hashed_password="hashed_password")
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_persona(db_session, test_user):
    # Create a test persona
    persona = Persona(user_id=test_user.id, name="Test Persona", description="Test persona description")
    db_session.add(persona)
    db_session.commit()
    return persona

@pytest.fixture
def test_linkedin_account(db_session, test_user):
    # Create a test LinkedIn account
    account = LinkedInAccount(
        user_id=test_user.id,
        access_token="test_access_token",
        profile_id="test_profile_id",
        profile_url="https://linkedin.com/in/testprofile"
    )
    db_session.add(account)
    db_session.commit()
    return account

@pytest.fixture
def test_post(db_session, test_user, test_persona):
    # Create a test post
    post = Post(
        user_id=test_user.id,
        persona_id=test_persona.id,
        content="Test post content",
        tone=PostTone.PROFESSIONAL,
        status=PostStatus.DRAFT,
        source_type="text",
        source_data={"text": "Original text for the post"}
    )
    db_session.add(post)
    db_session.commit()
    return post

def test_schedule_post(db_session, test_user, test_post, test_linkedin_account, monkeypatch):
    # Mock the dependency to return our test user
    monkeypatch.setattr("app.routers.scheduler.get_current_active_user", override_get_current_active_user)
    
    # Schedule the post
    scheduled_time = datetime.now() + timedelta(days=1)
    response = client.post(
        "/scheduler/schedule",
        json={
            "post_id": test_post.id,
            "scheduled_time": scheduled_time.isoformat(),
            "linkedin_account_id": test_linkedin_account.id
        }
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["post_id"] == test_post.id
    assert data["status"] == PostStatus.SCHEDULED
    
    # Verify database update
    updated_post = db_session.query(Post).filter(Post.id == test_post.id).first()
    assert updated_post.status == PostStatus.SCHEDULED
    assert updated_post.linkedin_account_id == test_linkedin_account.id

def test_get_scheduled_posts(db_session, test_user, test_post, test_linkedin_account, monkeypatch):
    # Set post as scheduled
    scheduled_time = datetime.now() + timedelta(days=1)
    test_post.status = PostStatus.SCHEDULED
    test_post.scheduled_time = scheduled_time
    test_post.linkedin_account_id = test_linkedin_account.id
    db_session.commit()
    
    # Mock the dependency to return our test user
    monkeypatch.setattr("app.routers.scheduler.get_current_active_user", override_get_current_active_user)
    
    # Get scheduled posts
    response = client.get("/scheduler/scheduled")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == test_post.id
    assert data[0]["status"] == PostStatus.SCHEDULED

def test_cancel_scheduled_post(db_session, test_user, test_post, test_linkedin_account, monkeypatch):
    # Set post as scheduled
    scheduled_time = datetime.now() + timedelta(days=1)
    test_post.status = PostStatus.SCHEDULED
    test_post.scheduled_time = scheduled_time
    test_post.linkedin_account_id = test_linkedin_account.id
    db_session.commit()
    
    # Mock the dependency to return our test user
    monkeypatch.setattr("app.routers.scheduler.get_current_active_user", override_get_current_active_user)
    
    # Cancel scheduled post
    response = client.delete(f"/scheduler/cancel/{test_post.id}")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_post.id
    assert data["status"] == PostStatus.DRAFT
    
    # Verify database update
    updated_post = db_session.query(Post).filter(Post.id == test_post.id).first()
    assert updated_post.status == PostStatus.DRAFT
    assert updated_post.scheduled_time is None

def test_reschedule_post(db_session, test_user, test_post, test_linkedin_account, monkeypatch):
    # Set post as scheduled
    scheduled_time = datetime.now() + timedelta(days=1)
    test_post.status = PostStatus.SCHEDULED
    test_post.scheduled_time = scheduled_time
    test_post.linkedin_account_id = test_linkedin_account.id
    db_session.commit()
    
    # Mock the dependency to return our test user
    monkeypatch.setattr("app.routers.scheduler.get_current_active_user", override_get_current_active_user)
    
    # Reschedule post
    new_scheduled_time = datetime.now() + timedelta(days=2)
    response = client.put(
        f"/scheduler/reschedule/{test_post.id}",
        json={
            "post_id": test_post.id,
            "scheduled_time": new_scheduled_time.isoformat(),
            "linkedin_account_id": test_linkedin_account.id
        }
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["post_id"] == test_post.id
    assert data["status"] == PostStatus.SCHEDULED
    
    # Verify database update
    updated_post = db_session.query(Post).filter(Post.id == test_post.id).first()
    assert updated_post.status == PostStatus.SCHEDULED
    # Check that the scheduled time was updated (approximately)
    time_diff = updated_post.scheduled_time - new_scheduled_time
    assert abs(time_diff.total_seconds()) < 5  # Allow for small differences in time precision