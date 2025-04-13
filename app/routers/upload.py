from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.models import User
from app.auth import get_current_active_user
from app.ai.document_processor import DocumentProcessor

router = APIRouter(
    prefix="/upload",
    tags=["File Upload"],
    responses={404: {"description": "Not found"}},
)

@router.post("/document", response_model=Dict[str, Any])
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload and process a document for content generation
    
    This endpoint handles document uploads (PDF, DOCX, TXT), processes them
    and returns the extracted text content along with metadata.
    
    Args:
        file: The uploaded file
        current_user: The authenticated user
        db: Database session
        
    Returns:
        Dict containing extracted text and metadata
    """
    try:
        # Process the uploaded file
        file_data = await DocumentProcessor.process_file(file)
        
        return {
            "status": "success",
            "message": "File processed successfully",
            "data": file_data
        }
        
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )