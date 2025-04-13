import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from dotenv import load_dotenv
import openai
from fastapi import HTTPException, status
import httpx
from newspaper import Article
from bs4 import BeautifulSoup

from app.models import PostTone
from app.ai.groq_client import groq_client

# Load environment variables
load_dotenv()

# Configure OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Determine which AI provider to use
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()  # Default to OpenAI if not specified

class ContentGenerator:
    """Class for generating LinkedIn post content using AI"""
    
    def __init__(self):
        self.provider = AI_PROVIDER
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "1000"))
    
    async def generate_from_bullet_points(self, 
                                    bullet_points: List[str], 
                                    tone: PostTone,
                                    persona_description: Optional[str] = None) -> str:
        """Generate a LinkedIn post from bullet points"""
        
        # Create prompt based on tone and persona
        prompt = self._create_prompt_from_bullets(bullet_points, tone, persona_description)
        
        # Generate content using OpenAI
        return await self._generate_content(prompt)
    
    async def generate_from_text(self, 
                          text: str, 
                          tone: PostTone,
                          persona_description: Optional[str] = None) -> str:
        """Generate a LinkedIn post from text content"""
        
        # Create prompt based on tone and persona
        prompt = self._create_prompt_from_text(text, tone, persona_description)
        
        # Generate content using AI
        return await self._generate_content(prompt)
    
    async def generate_from_file(self,
                          file_data: Dict[str, Any],
                          tone: PostTone,
                          persona_description: Optional[str] = None) -> str:
        """Generate a LinkedIn post from file content
        
        Args:
            file_data: Dictionary containing extracted text and metadata from file
            tone: Desired tone of the generated content
            persona_description: Optional persona description to guide content style
            
        Returns:
            str: Generated LinkedIn post content
        """
        # Extract text content from file data
        text = file_data.get("text", "")
        if not text:
            raise ValueError("No text content found in file data")
            
        # Create prompt based on tone and persona
        prompt = self._create_prompt_from_text(text, tone, persona_description)
        
        # Generate content using AI
        return await self._generate_content(prompt)
    
    async def generate_content(self, source_type: str, source_data: str, tone: PostTone) -> str:
        """Generate content based on source type and data"""
        if source_type == 'blog':
            return await self.generate_from_text(source_data, tone)
        elif source_type == 'text':
            return await process_text_content(source_data, tone)
        elif source_type == 'url':
            return await self.generate_from_url(source_data, tone)
        elif source_type == 'file':
            return await self.generate_from_file({'text': source_data}, tone)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

    async def generate_from_url(self, 
                         url: str, 
                         tone: PostTone,
                         persona_description: Optional[str] = None) -> str:
        """Generate a LinkedIn post from a URL"""
        try:
            # Extract content from the URL
            extracted_text = await self._extract_content_from_url(url)
            
            if not extracted_text or extracted_text == f"Content from: {url}\n\nUnable to extract detailed content.":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not extract content from the provided URL"
                )
            
            # Create prompt based on tone and persona
            prompt = self._create_prompt_from_text(extracted_text, tone, persona_description)
            
            # Generate content using AI
            return await self._generate_content(prompt)
            
        except HTTPException as e:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error processing URL: {str(e)}"
            )
    
    async def _extract_content_from_url(self, url: str) -> str:
        """Extract content from a URL using newspaper3k and BeautifulSoup"""
        try:
            # First try using newspaper3k which is good for article extraction
            article = Article(url)
            article.download()
            article.parse()
            
            # If we have a title and text, use newspaper3k results
            if article.title and article.text:
                content = f"Title: {article.title}\n\n"
                if article.meta_description:
                    content += f"Description: {article.meta_description}\n\n"
                content += article.text[:2000]  # Limit text length
                return content
                
        except Exception as newspaper_error:
            print(f"Newspaper3k extraction failed: {str(newspaper_error)}")
            
        # Fallback to basic httpx + BeautifulSoup extraction
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract title
                title = soup.title.string if soup.title else ""
                
                # Extract meta description
                meta_desc = ""
                meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
                if meta_tag and meta_tag.get("content"):
                    meta_desc = meta_tag.get("content")
                
                # Extract main content (this is a simple approach)
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.extract()
                
                # Get text and clean it up
                text = soup.get_text(separator="\n", strip=True)
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                text = "\n".join(lines)
                
                content = f"Title: {title}\n\n"
                if meta_desc:
                    content += f"Description: {meta_desc}\n\n"
                content += text[:2000]  # Limit text length
                
                return content
                
        except Exception as e:
            print(f"Error extracting content from URL: {str(e)}")
            # Return empty string to trigger 400 error
            return ""
    
    def _create_prompt_from_bullets(self, 
                               bullet_points: List[str], 
                               tone: PostTone,
                               persona_description: Optional[str] = None) -> str:
        """Create a prompt for the AI model from bullet points"""
        
        bullets_text = "\n".join([f"- {point}" for point in bullet_points])
        
        prompt = f"""Create an engaging LinkedIn post based on the following bullet points:

{bullets_text}

"""
        
        # Add tone and persona instructions
        prompt += self._get_tone_and_persona_instructions(tone, persona_description)
        
        return prompt
    
    def _create_prompt_from_text(self, 
                            text: str, 
                            tone: PostTone,
                            persona_description: Optional[str] = None) -> str:
        """Create a prompt for the AI model from text"""
        
        prompt = f"""Create an engaging LinkedIn post based on the following content:

{text}

"""
        
        # Add tone and persona instructions
        prompt += self._get_tone_and_persona_instructions(tone, persona_description)
        
        return prompt
    
    def _get_tone_and_persona_instructions(self, 
                                     tone: PostTone,
                                     persona_description: Optional[str] = None) -> str:
        """Get instructions for tone and persona"""
        
        tone_instructions = {
            PostTone.PROFESSIONAL: "Write in a professional and formal tone suitable for a business audience.",
            PostTone.INSPIRATIONAL: "Write in an inspirational and motivational tone that inspires action and positive thinking.",
            PostTone.STORYTELLING: "Write in a narrative storytelling style that engages readers with a personal touch.",
            PostTone.HUMOROUS: "Write with appropriate humor and a light-hearted tone while maintaining professionalism."
        }
        
        instructions = f"Tone: {tone_instructions.get(tone, tone_instructions[PostTone.PROFESSIONAL])}\n\n"
        
        if persona_description:
            instructions += f"Persona: Write as if you are {persona_description}\n\n"
        
        instructions += """Format Guidelines:
1. Keep the post between 1000-1300 characters
2. Use appropriate line breaks for readability
3. Include 2-3 relevant hashtags at the end
4. Avoid using excessive emojis or unprofessional language
5. End with a clear call-to-action or thought-provoking question"""
        
        return instructions
    
    async def _generate_content(self, prompt: str) -> str:
        """Generate content using selected AI provider (OpenAI or Groq)"""
        try:
            system_message = "You are an expert LinkedIn content creator who specializes in creating engaging and professional posts."
            temperature = 0.7
            
            if self.provider == "groq":
                return await groq_client.generate_completion(
                    prompt=prompt,
                    system_message=system_message,
                    temperature=temperature
                )
            else:
                client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                response = await client.chat.completions.create(
                    model=self.openai_model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating content with {self.provider}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate content using {self.provider}. Please try again later."
            )

# Create a singleton instance
content_generator = ContentGenerator()

async def process_text_content(text: str, tone: str) -> str:
    """Process raw text input into social media content"""
    prompt = content_generator._create_prompt_from_text(text, tone)
    return await content_generator._generate_content(prompt)