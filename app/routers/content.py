from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.database import get_db
from app.models import User, Persona, Post, PostTone, PostStatus
from app.schemas import ContentGenerationRequest, ContentGenerationResponse, PostCreate, Post as PostSchema
from app.auth import get_current_active_user
from app.ai.content_generator import content_generator
from app.ai.document_processor import DocumentProcessor

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
    
    # Validate source type first
    if request.source_type not in ["bullet_points", "text", "url", "file"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported source type: {request.source_type}"
        )
    
    try:
        # Generate content based on source type
        if request.source_type == "bullet_points":
            # Validate bullet points
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
            # Validate text content
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
            
        elif request.source_type == "file":
            # File content should already be processed and stored in source_data
            file_data = request.source_data
            if not file_data or "text" not in file_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid file data provided"
                )
            
            content = await content_generator.generate_from_file(
                file_data=file_data,
                tone=request.tone,
                persona_description=persona_description
            )
            
        else:  # URL type
            # Validate URL
            url = request.source_data.get("url", "")
            if not url:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No URL provided"
                )
            
            try:
                content = await content_generator.generate_from_url(
                    url=url,
                    tone=request.tone,
                    persona_description=persona_description
                )
            except HTTPException as e:
                # Pass through HTTP exceptions from content generator
                raise e
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error processing URL: {str(e)}"
                )
        
        return ContentGenerationResponse(
            content=content,
            tone=request.tone,
            source_type=request.source_type,
            source_data=request.source_data
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors and return 500
        logger.error(f"Unexpected error generating content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating content"
        )

@router.post("/upload", response_model=ContentGenerationResponse)
async def upload_file(
    file: UploadFile = File(...),
    tone: PostTone = None,
    persona_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a file and generate LinkedIn post content from it"""
    
    # Check if persona exists and belongs to user if provided
    persona_description = None
    if persona_id:
        persona = db.query(Persona).filter(
            Persona.id == persona_id,
            Persona.user_id == current_user.id
        ).first()
        
        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Persona not found or does not belong to current user"
            )
        
        persona_description = persona.description
    
    try:
        # Process the uploaded file
        file_data = await DocumentProcessor.process_file(file)
        
        # Generate content from the processed file
        content = await content_generator.generate_from_file(
            file_data=file_data,
            tone=tone or PostTone.PROFESSIONAL,  # Default to professional tone if not specified
            persona_description=persona_description
        )
        
        return ContentGenerationResponse(
            content=content,
            tone=tone or PostTone.PROFESSIONAL,
            source_type="file",
            source_data=file_data
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing file upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the file"
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