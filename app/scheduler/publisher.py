from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
import asyncio
import time

from app.models import Post, PostStatus
from app.database import SessionLocal
from app.linkedin.client import LinkedInClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostPublisher:
    """Handles the publishing of scheduled posts to LinkedIn"""
    
    def __init__(self, check_interval: int = 60):
        """Initialize the post publisher
        
        Args:
            check_interval: How often to check for posts to publish (in seconds)
        """
        self.check_interval = check_interval
        self.is_running = False
    
    async def start(self):
        """Start the post publisher background task"""
        self.is_running = True
        logger.info("Starting post publisher background task")
        
        while self.is_running:
            try:
                await self.process_scheduled_posts()
            except Exception as e:
                logger.error(f"Error processing scheduled posts: {str(e)}")
            
            # Wait for the next check interval
            await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop the post publisher background task"""
        self.is_running = False
        logger.info("Stopping post publisher background task")
    
    async def process_scheduled_posts(self):
        """Process all scheduled posts that are due for publishing"""
        # Get current time
        now = datetime.now()
        
        # Create a database session
        db = SessionLocal()
        
        try:
            # Find all scheduled posts that are due for publishing
            due_posts = db.query(Post).filter(
                Post.status == PostStatus.SCHEDULED,
                Post.scheduled_time <= now
            ).all()
            
            if due_posts:
                logger.info(f"Found {len(due_posts)} posts due for publishing")
            
            # Process each due post
            for post in due_posts:
                try:
                    await self.publish_post(db, post)
                except Exception as e:
                    logger.error(f"Error publishing post {post.id}: {str(e)}")
                    # Mark post as failed
                    post.status = PostStatus.FAILED
                    db.commit()
        
        finally:
            # Close the database session
            db.close()
    
    async def publish_post(self, db: Session, post: Post):
        """Publish a post to LinkedIn
        
        Args:
            db: Database session
            post: Post to publish
        """
        logger.info(f"Publishing post {post.id} to LinkedIn")
        
        try:
            # Check if post has a LinkedIn account associated
            if not post.linkedin_account_id:
                raise ValueError("Post does not have a LinkedIn account associated")
            
            # Get the LinkedIn account
            linkedin_account = post.linkedin_account
            
            # Create LinkedIn client
            linkedin_client = LinkedInClient(
                access_token=linkedin_account.access_token,
                refresh_token=linkedin_account.refresh_token,
                token_expires_at=linkedin_account.token_expires_at
            )
            
            # Publish post to LinkedIn
            post_id = await linkedin_client.publish_post(post.content)
            
            # Update post with LinkedIn post ID and status
            post.linkedin_post_id = post_id
            post.status = PostStatus.PUBLISHED
            post.published_time = datetime.now()
            
            # If token was refreshed, update the account
            if linkedin_client.token_refreshed:
                linkedin_account.access_token = linkedin_client.access_token
                linkedin_account.refresh_token = linkedin_client.refresh_token
                linkedin_account.token_expires_at = linkedin_client.token_expires_at
            
            # Commit changes to database
            db.commit()
            
            logger.info(f"Successfully published post {post.id} to LinkedIn")
            
        except Exception as e:
            logger.error(f"Error publishing post {post.id} to LinkedIn: {str(e)}")
            # Mark post as failed
            post.status = PostStatus.FAILED
            db.commit()
            # Re-raise exception for the caller to handle
            raise

# Create a singleton instance
post_publisher = PostPublisher()