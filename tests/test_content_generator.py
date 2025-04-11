import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException

from app.ai.content_generator import ContentGenerator
from app.models import PostTone

# Setup test fixtures
@pytest.fixture
def content_generator():
    return ContentGenerator()

# Mock environment variables for testing
@pytest.fixture(autouse=True)
def mock_env_variables(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test_api_key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-3.5-turbo")
    monkeypatch.setenv("MAX_TOKENS", "500")
    monkeypatch.setenv("AI_PROVIDER", "openai")

# Test initialization
def test_content_generator_init(content_generator):
    assert content_generator.provider == "openai"
    assert content_generator.openai_model == "gpt-3.5-turbo"
    assert content_generator.max_tokens == 500

# Test prompt creation from bullet points
def test_create_prompt_from_bullets(content_generator):
    bullet_points = ["Point 1", "Point 2", "Point 3"]
    tone = PostTone.PROFESSIONAL
    persona = "a tech industry expert"
    
    prompt = content_generator._create_prompt_from_bullets(bullet_points, tone, persona)
    
    # Check that the prompt contains all bullet points
    for point in bullet_points:
        assert f"- {point}" in prompt
    
    # Check that tone and persona are included
    assert "professional" in prompt.lower()
    assert persona in prompt

# Test prompt creation from text
def test_create_prompt_from_text(content_generator):
    text = "Sample text for testing"
    tone = PostTone.INSPIRATIONAL
    persona = "a motivational speaker"
    
    prompt = content_generator._create_prompt_from_text(text, tone, persona)
    
    # Check that the prompt contains the text
    assert text in prompt
    
    # Check that tone and persona are included
    assert "inspirational" in prompt.lower()
    assert persona in prompt

# Test tone and persona instructions
def test_get_tone_and_persona_instructions(content_generator):
    # Test professional tone
    instructions = content_generator._get_tone_and_persona_instructions(PostTone.PROFESSIONAL)
    assert "professional" in instructions.lower()
    
    # Test with persona
    persona = "a tech industry expert"
    instructions = content_generator._get_tone_and_persona_instructions(PostTone.STORYTELLING, persona)
    assert "storytelling" in instructions.lower()
    assert persona in instructions
    
    # Check format guidelines are included
    assert "Format Guidelines:" in instructions
    assert "hashtags" in instructions

# Test content generation with OpenAI
@pytest.mark.asyncio
async def test_generate_content_openai(content_generator):
    prompt = "Test prompt"
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Generated content"
    
    with patch('openai.ChatCompletion.acreate', new_callable=AsyncMock) as mock_openai:
        mock_openai.return_value = mock_response
        result = await content_generator._generate_content(prompt)
        
        # Check that OpenAI was called with correct parameters
        mock_openai.assert_called_once()
        call_args = mock_openai.call_args[1]
        assert call_args['model'] == "gpt-3.5-turbo"
        assert call_args['max_tokens'] == 500
        assert call_args['messages'][1]['content'] == prompt
        
        # Check result
        assert result == "Generated content"

# Test content generation with Groq
@pytest.mark.asyncio
async def test_generate_content_groq(content_generator):
    prompt = "Test prompt"
    content_generator.provider = "groq"
    
    with patch('app.ai.groq_client.groq_client.generate_completion', new_callable=AsyncMock) as mock_groq:
        mock_groq.return_value = "Generated content from Groq"
        result = await content_generator._generate_content(prompt)
        
        # Check that Groq was called with correct parameters
        mock_groq.assert_called_once_with(
            prompt=prompt,
            system_message="You are an expert LinkedIn content creator who specializes in creating engaging and professional posts.",
            temperature=0.7
        )
        
        # Check result
        assert result == "Generated content from Groq"

# Test error handling in content generation
@pytest.mark.asyncio
async def test_generate_content_error(content_generator):
    prompt = "Test prompt"
    
    with patch('openai.ChatCompletion.acreate', new_callable=AsyncMock) as mock_openai:
        mock_openai.side_effect = Exception("API error")
        
        with pytest.raises(HTTPException) as excinfo:
            await content_generator._generate_content(prompt)
        
        assert excinfo.value.status_code == 500
        assert "Failed to generate content" in str(excinfo.value.detail)

# Test URL content extraction
@pytest.mark.asyncio
async def test_extract_content_from_url(content_generator):
    url = "https://example.com"
    mock_article = MagicMock()
    mock_article.title = "Test Article"
    mock_article.meta_description = "Test Description"
    mock_article.text = "Article content for testing"
    
    with patch('newspaper.Article', return_value=mock_article) as mock_newspaper:
        result = await content_generator._extract_content_from_url(url)
        
        # Check that Article was initialized with the URL
        mock_newspaper.assert_called_once_with(url)
        
        # Check that the article methods were called
        mock_article.download.assert_called_once()
        mock_article.parse.assert_called_once()
        
        # Check result contains article information
        assert "Title: Test Article" in result
        assert "Description: Test Description" in result
        assert "Article content for testing" in result

# Test URL content extraction fallback
@pytest.mark.asyncio
async def test_extract_content_from_url_fallback(content_generator):
    url = "https://example.com"
    
    # Mock newspaper to fail
    with patch('newspaper.Article', side_effect=Exception("Newspaper error")):
        # Mock httpx client
        mock_response = MagicMock()
        mock_response.text = "<html><head><title>Test Page</title><meta name='description' content='Test Meta'></head><body>Test content</body></html>"
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get.return_value = mock_response
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            with patch('bs4.BeautifulSoup') as mock_bs:
                mock_soup = MagicMock()
                mock_soup.title.string = "Test Page"
                mock_soup.find.return_value.get.return_value = "Test Meta"
                mock_soup.get_text.return_value = "Test content"
                mock_bs.return_value = mock_soup
                
                result = await content_generator._extract_content_from_url(url)
                
                # Check result contains fallback information
                assert "Title: Test Page" in result
                assert "Description: Test Meta" in result
                assert "Test content" in result

# Test generate from bullet points
@pytest.mark.asyncio
async def test_generate_from_bullet_points(content_generator):
    bullet_points = ["Point 1", "Point 2"]
    tone = PostTone.PROFESSIONAL
    persona = "a tech expert"
    
    with patch.object(content_generator, '_create_prompt_from_bullets', return_value="Test prompt") as mock_create_prompt:
        with patch.object(content_generator, '_generate_content', new_callable=AsyncMock, return_value="Generated content") as mock_generate:
            result = await content_generator.generate_from_bullet_points(bullet_points, tone, persona)
            
            # Check that methods were called with correct parameters
            mock_create_prompt.assert_called_once_with(bullet_points, tone, persona)
            mock_generate.assert_called_once_with("Test prompt")
            
            # Check result
            assert result == "Generated content"

# Test generate from text
@pytest.mark.asyncio
async def test_generate_from_text(content_generator):
    text = "Test text"
    tone = PostTone.STORYTELLING
    persona = "a storyteller"
    
    with patch.object(content_generator, '_create_prompt_from_text', return_value="Test prompt") as mock_create_prompt:
        with patch.object(content_generator, '_generate_content', new_callable=AsyncMock, return_value="Generated content") as mock_generate:
            result = await content_generator.generate_from_text(text, tone, persona)
            
            # Check that methods were called with correct parameters
            mock_create_prompt.assert_called_once_with(text, tone, persona)
            mock_generate.assert_called_once_with("Test prompt")
            
            # Check result
            assert result == "Generated content"

# Test generate from URL
@pytest.mark.asyncio
async def test_generate_from_url(content_generator):
    url = "https://example.com"
    tone = PostTone.HUMOROUS
    persona = "a comedian"
    
    with patch.object(content_generator, '_extract_content_from_url', new_callable=AsyncMock, return_value="Extracted content") as mock_extract:
        with patch.object(content_generator, '_create_prompt_from_text', return_value="Test prompt") as mock_create_prompt:
            with patch.object(content_generator, '_generate_content', new_callable=AsyncMock, return_value="Generated content") as mock_generate:
                result = await content_generator.generate_from_url(url, tone, persona)
                
                # Check that methods were called with correct parameters
                mock_extract.assert_called_once_with(url)
                mock_create_prompt.assert_called_once_with("Extracted content", tone, persona)
                mock_generate.assert_called_once_with("Test prompt")
                
                # Check result
                assert result == "Generated content"

# Test generate from URL with extraction failure
@pytest.mark.asyncio
async def test_generate_from_url_extraction_failure(content_generator):
    url = "https://example.com"
    tone = PostTone.PROFESSIONAL
    
    with patch.object(content_generator, '_extract_content_from_url', new_callable=AsyncMock, return_value="") as mock_extract:
        with pytest.raises(HTTPException) as excinfo:
            await content_generator.generate_from_url(url, tone)
        
        assert excinfo.value.status_code == 400
        assert "Could not extract content" in str(excinfo.value.detail)