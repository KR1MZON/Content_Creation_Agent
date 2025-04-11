import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.orm import Session

from main import app
from app.models import User, Persona, PostTone, PostStatus
from app.database import get_db
from app.auth import get_current_active_user

# Setup test client
@pytest.fixture
def client():
    return TestClient(app)

# Mock authenticated user
@pytest.fixture
def mock_current_user():
    user = User()
    user.id = 1
    user.email = "test@example.com"
    user.username = "testuser"
    user.full_name = "Test User"
    user.is_active = True
    return user

# Mock database session
@pytest.fixture
def mock_db():
    db = MagicMock(spec=Session)
    return db

# Override dependencies
@pytest.fixture(autouse=True)
def override_dependencies(mock_current_user, mock_db):
    app.dependency_overrides[get_current_active_user] = lambda: mock_current_user
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides = {}

# Test generate content endpoint with bullet points
def test_generate_content_bullet_points(client, mock_db, mock_current_user):
    # Mock persona
    mock_persona = MagicMock()
    mock_persona.id = 1
    mock_persona.user_id = mock_current_user.id
    mock_persona.description = "A tech industry expert"
    
    # Setup mock database query
    mock_db.query.return_value.filter.return_value.first.return_value = mock_persona
    
    # Mock content generator
    with patch('app.ai.content_generator.content_generator.generate_from_bullet_points', new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = "Generated LinkedIn post content"
        
        # Test request
        response = client.post(
            "/content/generate",
            json={
                "source_type": "bullet_points",
                "source_data": {"points": ["Point 1", "Point 2", "Point 3"]},
                "tone": "professional",
                "persona_id": 1
            }
        )
        
        # Check response
        assert response.status_code == 200
        assert response.json()["content"] == "Generated LinkedIn post content"
        assert response.json()["tone"] == "professional"
        assert response.json()["source_type"] == "bullet_points"
        
        # Verify mock calls
        mock_db.query.assert_called_once()
        mock_generate.assert_called_once_with(
            bullet_points=["Point 1", "Point 2", "Point 3"],
            tone=PostTone.PROFESSIONAL,
            persona_description="A tech industry expert"
        )

# Test generate content endpoint with text
def test_generate_content_text(client, mock_db):
    # Setup mock database query - no persona this time
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    # Mock content generator
    with patch('app.ai.content_generator.content_generator.generate_from_text', new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = "Generated LinkedIn post from text"
        
        # Test request
        response = client.post(
            "/content/generate",
            json={
                "source_type": "text",
                "source_data": {"text": "Sample text for content generation"},
                "tone": "inspirational",
                "persona_id": None
            }
        )
        
        # Check response
        assert response.status_code == 200
        assert response.json()["content"] == "Generated LinkedIn post from text"
        assert response.json()["tone"] == "inspirational"
        assert response.json()["source_type"] == "text"
        
        # Verify mock calls
        mock_generate.assert_called_once_with(
            text="Sample text for content generation",
            tone=PostTone.INSPIRATIONAL,
            persona_description=None
        )

# Test generate content endpoint with URL
def test_generate_content_url(client, mock_db):
    # Setup mock database query - no persona
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    # Mock content generator
    with patch('app.ai.content_generator.content_generator.generate_from_url', new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = "Generated LinkedIn post from URL"
        
        # Test request
        response = client.post(
            "/content/generate",
            json={
                "source_type": "url",
                "source_data": {"url": "https://example.com"},
                "tone": "storytelling",
                "persona_id": None
            }
        )
        
        # Check response
        assert response.status_code == 200
        assert response.json()["content"] == "Generated LinkedIn post from URL"
        assert response.json()["tone"] == "storytelling"
        assert response.json()["source_type"] == "url"
        
        # Verify mock calls
        mock_generate.assert_called_once_with(
            url="https://example.com",
            tone=PostTone.STORYTELLING,
            persona_description=None
        )

# Test error handling - persona not found
def test_generate_content_persona_not_found(client, mock_db):
    # Setup mock database query - persona not found
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    # Test request with invalid persona ID
    response = client.post(
        "/content/generate",
        json={
            "source_type": "bullet_points",
            "source_data": {"points": ["Point 1", "Point 2"]},
            "tone": "professional",
            "persona_id": 999  # Non-existent persona
        }
    )
    
    # Check response
    assert response.status_code == 404
    assert "Persona not found" in response.json()["detail"]

# Test error handling - invalid source type
def test_generate_content_invalid_source_type(client):
    # Test request with invalid source type
    response = client.post(
        "/content/generate",
        json={
            "source_type": "invalid_type",
            "source_data": {"data": "some data"},
            "tone": "professional",
            "persona_id": None
        }
    )
    
    # Check response
    assert response.status_code == 400
    assert "Unsupported source type" in response.json()["detail"]

# Test error handling - missing data
def test_generate_content_missing_data(client):
    # Test request with missing bullet points
    response = client.post(
        "/content/generate",
        json={
            "source_type": "bullet_points",
            "source_data": {},  # Missing points
            "tone": "professional",
            "persona_id": None
        }
    )
    
    # Check response
    assert response.status_code == 400
    assert "No bullet points provided" in response.json()["detail"]
    
    # Test request with missing text
    response = client.post(
        "/content/generate",
        json={
            "source_type": "text",
            "source_data": {},  # Missing text
            "tone": "professional",
            "persona_id": None
        }
    )
    
    # Check response
    assert response.status_code == 400
    assert "No text content provided" in response.json()["detail"]
    
    # Test request with missing URL
    response = client.post(
        "/content/generate",
        json={
            "source_type": "url",
            "source_data": {},  # Missing URL
            "tone": "professional",
            "persona_id": None
        }
    )
    
    # Check response
    assert response.status_code == 400
    assert "No URL provided" in response.json()["detail"]