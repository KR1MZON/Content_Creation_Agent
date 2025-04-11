import os
import json
from typing import Dict, Any, Optional, List, AsyncGenerator

import httpx
from fastapi import HTTPException, status

from app.models import PostTone

# Hardcoded Groq API key
GROQ_API_KEY = "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"  # Replace with your actual Groq API key

class GroqClient:
    """Client for interacting with the Groq API for content generation"""
    
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        self.model = os.getenv("GROQ_MODEL", "llama3-70b-8192")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "1000"))
        self.timeout = float(os.getenv("GROQ_TIMEOUT", "60.0"))
        
        if not self.api_key:
            raise ValueError("Groq API key is not set")
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for Groq API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _create_chat_payload(self, prompt: str, system_message: Optional[str] = None, temperature: float = 0.7, stream: bool = False) -> Dict[str, Any]:
        """Create a payload for chat completion request"""
        system_content = system_message or "You are an expert LinkedIn content creator who specializes in creating engaging and professional posts."
        
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.max_tokens,
            "temperature": temperature,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stream": stream
        }
    
    async def generate_completion(self, prompt: str, system_message: Optional[str] = None, temperature: float = 0.7) -> str:
        """Generate content using Groq API"""
        try:
            headers = self._get_default_headers()
            payload = self._create_chat_payload(prompt, system_message, temperature)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    self._handle_error_response(response)
                
                response_data = response.json()
                generated_text = response_data["choices"][0]["message"]["content"].strip()
                return generated_text
                
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error connecting to Groq API: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate content: {str(e)}"
            )
    
    async def generate_completion_stream(self, prompt: str, system_message: Optional[str] = None, temperature: float = 0.7) -> AsyncGenerator[str, None]:
        """Generate content using Groq API with streaming response"""
        try:
            headers = self._get_default_headers()
            payload = self._create_chat_payload(prompt, system_message, temperature, stream=True)
            
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                ) as response:
                    if response.status_code != 200:
                        await response.aread()
                        self._handle_error_response(response)
                    
                    async for chunk in response.aiter_lines():
                        if not chunk.strip():
                            continue
                        
                        try:
                            chunk_data = json.loads(chunk.lstrip("data: ").strip())
                            if chunk_data.get("choices") and len(chunk_data["choices"]) > 0:
                                delta = chunk_data["choices"][0].get("delta", {})
                                if "content" in delta and delta["content"]:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
        
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error connecting to Groq API: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate streaming content: {str(e)}"
            )
    
    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from the Groq API"""
        try:
            error_data = response.json()
            error_detail = error_data.get("error", {}).get("message", "Unknown error")
            error_type = error_data.get("error", {}).get("type", "unknown_error")
            
            if response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Groq API authentication error: {error_detail}"
                )
            elif response.status_code == 429:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Groq API rate limit exceeded: {error_detail}"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Groq API error ({error_type}): {error_detail}"
                )
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Groq API error: Invalid response format (Status code: {response.status_code})"
            )

# Create a singleton instance
groq_client = GroqClient()