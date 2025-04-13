import os
from typing import Optional, Dict, Any
from fastapi import UploadFile, HTTPException, status
from PyPDF2 import PdfReader
from docx import Document
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Class for processing uploaded documents and extracting text content"""
    
    SUPPORTED_EXTENSIONS = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain'
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @classmethod
    async def process_file(cls, file: UploadFile) -> Dict[str, Any]:
        """Process an uploaded file and extract its content
        
        Args:
            file: The uploaded file
            
        Returns:
            Dict containing extracted text and metadata
        """
        try:
            # Read file content
            content = await file.read()
            
            # Check file size
            if len(content) > cls.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File size exceeds maximum limit of {cls.MAX_FILE_SIZE/1024/1024}MB"
                )
            
            # Get file extension and check if supported
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in cls.SUPPORTED_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type: {file_ext}"
                )
            
            mime_type = cls.SUPPORTED_EXTENSIONS[file_ext]
            
            # Process based on file type
            if file_ext == '.pdf':
                text = cls._process_pdf(content)
            elif file_ext == '.docx':
                text = cls._process_docx(content)
            else:  # .txt
                text = content.decode('utf-8')
            
            return {
                "text": text,
                "metadata": {
                    "file_type": file_ext[1:],  # Remove the dot
                    "file_name": file.filename,
                    "mime_type": mime_type
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error processing file: {str(e)}"
            )
        finally:
            await file.close()
    
    @staticmethod
    def _process_pdf(content: bytes) -> str:
        """Extract text from PDF content"""
        try:
            reader = PdfReader(content)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error processing PDF: {str(e)}")
    
    @staticmethod
    def _process_docx(content: bytes) -> str:
        """Extract text from DOCX content"""
        try:
            doc = Document(content)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error processing DOCX: {str(e)}")