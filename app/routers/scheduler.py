from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models import User, Post, PostStatus, LinkedInAccount
from app.schemas import SchedulePostRequest, SchedulePostResponse, Post as PostSchema
from app.auth import get_current_active_user

router = APIRouter(
    prefix="/scheduler",
    tags=["Post Scheduling"],
    responses={404: {"description": "Not found"}},
)

@router.post("/schedule", response_model=SchedulePostResponse)
async def schedule_post(
    request: SchedulePostRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Schedule a post for future publishing"""
    
    # Validate post exists and belongs to user
    post = db.query(Post).filter(
        Post.id == request.post_id,
        Post.user_id == current_user.id
    ).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found or does not belong to current user"
        )
    
    # Validate LinkedIn account exists and belongs to user
    linkedin_account = db.query(LinkedInAccount).filter(
        LinkedInAccount.id == request.linkedin_account_id,
        LinkedInAccount.user_id == current_user.id
    ).first()
    
    if not linkedin_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LinkedIn account not found or does not belong to current user"
        )
    
    # Validate scheduled time is in the future
    if request.scheduled_time <= datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduled time must be in the future"
        )
    
    # Update post with scheduling information
    post.status = PostStatus.SCHEDULED
    post.scheduled_time = request.scheduled_time
    post.linkedin_account_id = request.linkedin_account_id
    
    db.commit()
    db.refresh(post)
    
    return SchedulePostResponse(
        post_id=post.id,
        scheduled_time=post.scheduled_time,
        status=post.status
    )

@router.get("/scheduled", response_model=List[PostSchema])
async def get_scheduled_posts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all scheduled posts for the current user"""
    
    scheduled_posts = db.query(Post).filter(
        Post.user_id == current_user.id,
        Post.status == PostStatus.SCHEDULED
    ).all()
    
    return scheduled_posts

@router.delete("/cancel/{post_id}", response_model=PostSchema)
async def cancel_scheduled_post(
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel a scheduled post"""
    
    # Validate post exists and belongs to user
    post = db.query(Post).filter(
        Post.id == post_id,
        Post.user_id == current_user.id,
        Post.status == PostStatus.SCHEDULED
    ).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled post not found or does not belong to current user"
        )
    
    # Update post status to draft
    post.status = PostStatus.DRAFT
    post.scheduled_time = None
    
    db.commit()
    db.refresh(post)
    
    return post

@router.put("/reschedule/{post_id}", response_model=SchedulePostResponse)
async def reschedule_post(
    post_id: int,
    request: SchedulePostRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Reschedule an existing scheduled post"""
    
    # Validate post exists and belongs to user
    post = db.query(Post).filter(
        Post.id == post_id,
        Post.user_id == current_user.id,
        Post.status == PostStatus.SCHEDULED
    ).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled post not found or does not belong to current user"
        )
    
    # Validate LinkedIn account exists and belongs to user
    linkedin_account = db.query(LinkedInAccount).filter(
        LinkedInAccount.id == request.linkedin_account_id,
        LinkedInAccount.user_id == current_user.id
    ).first()
    
    if not linkedin_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LinkedIn account not found or does not belong to current user"
        )
    
    # Validate scheduled time is in the future
    if request.scheduled_time <= datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduled time must be in the future"
        )
    
    # Update post with new scheduling information
    post.scheduled_time = request.scheduled_time
    post.linkedin_account_id = request.linkedin_account_id
    
    db.commit()
    db.refresh(post)
    
    return SchedulePostResponse(
        post_id=post.id,
        scheduled_time=post.scheduled_time,
        status=post.status
    )