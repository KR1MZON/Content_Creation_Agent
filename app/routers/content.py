from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.database import get_db
from app.models import User, Persona, Post, PostTone, PostStatus
from app.schemas import ContentGenerationRequest, ContentGenerationResponse, PostCreate, Post as PostSchema
from app.auth import get_current_active_user
from app.ai.content_generator import content_generator

router = APIRouter(
    prefix="/content",
    tags=["Content Generation"],
    responses={404: {"description": "Not found"}},
)

@router.post("/generate", response_model=ContentGenerationResponse)
async def generate_content(
    request: ContentGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate LinkedIn post content based on provided source data"""
    
    # Check if persona exists and belongs to user if provided
    persona_description = None
    if request.persona_id:
        persona = db.query(Persona).filter(
            Persona.id == request.persona_id,
            Persona.user_id == current_user.id
        ).first()
        
        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Persona not found or does not belong to current user"
            )
        
        persona_description = persona.description
    
    # Generate content based on source type
    try:
        if request.source_type == "bullet_points":
            # Expect source_data to contain a list of bullet points
            bullet_points = request.source_data.get("points", [])
            if not bullet_points:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No bullet points provided"
                )
            
            content = await content_generator.generate_from_bullet_points(
                bullet_points=bullet_points,
                tone=request.tone,
                persona_description=persona_description
            )
            
        elif request.source_type == "text":
            # Expect source_data to contain text content
            text = request.source_data.get("text", "")
            if not text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No text content provided"
                )
            
            content = await content_generator.generate_from_text(
                text=text,
                tone=request.tone,
                persona_description=persona_description
            )
            
        elif request.source_type == "url":
            # Expect source_data to contain a URL
            url = request.source_data.get("url", "")
            if not url:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No URL provided"
                )
            
            content = await content_generator.generate_from_url(
                url=url,
                tone=request.tone,
                persona_description=persona_description
            )
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported source type: {request.source_type}"
            )
            
        return ContentGenerationResponse(
            content=content,
            tone=request.tone,
            source_type=request.source_type,
            source_data=request.source_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating content: {str(e)}"
        )

@router.post("/save", response_model=PostSchema)
async def save_generated_content(
    post: PostCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Save generated content as a post"""
    
    # Validate persona if provided
    if post.persona_id:
        persona = db.query(Persona).filter(
            Persona.id == post.persona_id,
            Persona.user_id == current_user.id
        ).first()
        
        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Persona not found or does not belong to current user"
            )
    
    # Validate LinkedIn account if provided
    if post.linkedin_account_id:
        linkedin_account = db.query(LinkedInAccount).filter(
            LinkedInAccount.id == post.linkedin_account_id,
            LinkedInAccount.user_id == current_user.id
        ).first()
        
        if not linkedin_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LinkedIn account not found or does not belong to current user"
            )
    
    # Create new post
    db_post = Post(
        user_id=current_user.id,
        content=post.content,
        tone=post.tone,
        persona_id=post.persona_id,
        linkedin_account_id=post.linkedin_account_id,
        source_type=post.source_type,
        source_data=post.source_data,
        status=PostStatus.DRAFT
    )
    
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    return db_post