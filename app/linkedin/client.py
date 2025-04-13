import httpx
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LinkedInClient:
    """Client for interacting with LinkedIn API"""
    
    def __init__(self, access_token: str, refresh_token: Optional[str] = None, token_expires_at: Optional[datetime] = None):
        """Initialize LinkedIn client
        
        Args:
            access_token: LinkedIn API access token
            refresh_token: LinkedIn API refresh token (optional)
            token_expires_at: When the access token expires (optional)
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = token_expires_at
        self.token_refreshed = False
        self.base_url = "https://api.linkedin.com/v2"
        
    async def publish_post(self, content: str) -> str:
        """Publish a text post to LinkedIn
        
        Args:
            content: The text content to post
            
        Returns:
            str: The LinkedIn post ID
        """
        # Check if token needs refreshing
        await self._refresh_token_if_needed()
        
        # Prepare the post data
        # This is a simplified version - actual LinkedIn API requires more structured data
        post_data = {
            "author": "urn:li:person:{person_id}",  # Will be replaced with actual person ID
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        try:
            # Get user profile to get person ID
            profile = await self._get_user_profile()
            person_id = profile.get("id")
            
            if not person_id:
                raise ValueError("Could not retrieve LinkedIn person ID")
            
            # Replace placeholder with actual person ID
            post_data["author"] = f"urn:li:person:{person_id}"
            
            # Make API request to create post
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/ugcPosts",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json",
                        "X-Restli-Protocol-Version": "2.0.0"
                    },
                    json=post_data
                )
                
                response.raise_for_status()
                
                # Extract post ID from response
                # The response format depends on LinkedIn API version
                # This is a simplified example
                post_id = response.headers.get("x-restli-id") or "unknown_post_id"
                
                logger.info(f"Successfully published post to LinkedIn with ID: {post_id}")
                return post_id
                
        except httpx.HTTPStatusError as e:
            logger.error(f"LinkedIn API error: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"LinkedIn API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Error publishing post to LinkedIn: {str(e)}")
            raise
    
    async def _get_user_profile(self) -> dict:
        """Get the user's LinkedIn profile
        
        Returns:
            dict: User profile data
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/me",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "X-Restli-Protocol-Version": "2.0.0"
                    }
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"LinkedIn API error getting profile: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"LinkedIn API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Error getting LinkedIn profile: {str(e)}")
            raise
    
    async def _refresh_token_if_needed(self) -> None:
        """Refresh the access token if it's expired or about to expire"""
        # Check if we have refresh token and expiration time
        if not self.refresh_token or not self.token_expires_at:
            return
        
        # Check if token is expired or about to expire (within 5 minutes)
        if datetime.now() >= self.token_expires_at - timedelta(minutes=5):
            await self._refresh_token()
    
    async def _refresh_token(self) -> None:
        """Refresh the LinkedIn access token"""
        try:
            # This is a simplified example - actual implementation depends on LinkedIn OAuth flow
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://www.linkedin.com/oauth/v2/accessToken",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": self.refresh_token,
                        "client_id": "YOUR_CLIENT_ID",  # Should be retrieved from environment variables
                        "client_secret": "YOUR_CLIENT_SECRET"  # Should be retrieved from environment variables
                    },
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded"
                    }
                )
                
                response.raise_for_status()
                token_data = response.json()
                
                # Update tokens
                self.access_token = token_data["access_token"]
                if "refresh_token" in token_data:
                    self.refresh_token = token_data["refresh_token"]
                
                # Update expiration time
                expires_in = token_data.get("expires_in", 3600)  # Default to 1 hour
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # Set flag indicating token was refreshed
                self.token_refreshed = True
                
                logger.info("Successfully refreshed LinkedIn access token")
                
        except Exception as e:
            logger.error(f"Error refreshing LinkedIn token: {str(e)}")
            # Continue with existing token and hope for the best
            pass