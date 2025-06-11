import os
import uuid
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from datetime import datetime

from models.document import (
    UploadResponse, StatusResponse, ProcessingResult, 
    CorrectionRequest, GroundingResponse, BoundingBox
)
from services.storage import storage
from services.document_processor import processor
from agents.simple_workflow import workflow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["documents"])

# Create upload directory
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload and process a document"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not processor.is_supported_format(file.filename):
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file format. Supported: PDF, PNG, JPEG"
            )
        
        # Check file size (50MB limit)
        max_size = int(os.getenv("MAX_FILE_SIZE", 50000000))
        if file.size and file.size > max_size:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size: {max_size/1000000}MB"
            )
        
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        saved_filename = f"{file_id}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, saved_filename)
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Start background processing
        background_tasks.add_task(
            process_document_background, 
            file_path, 
            file.filename
        )
        
        logger.info(f"File uploaded: {file.filename} -> {saved_filename}")
        
        return UploadResponse(
            transaction_id=file_id,
            status="pending",
            message="Document uploaded successfully. Processing started."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def process_document_background(file_path: str, filename: str):
    """Background task for document processing"""
    try:
        transaction_id = await workflow.process_document(file_path, filename)
        logger.info(f"Background processing completed for: {transaction_id}")
    except Exception as e:
        logger.error(f"Background processing error: {e}")


@router.get("/status/{transaction_id}", response_model=StatusResponse)
async def get_processing_status(transaction_id: str):
    """Get processing status for a transaction"""
    try:
        result = await storage.get_result(transaction_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Calculate progress based on status
        progress_map = {
            "pending": 0,
            "parsing": 20,
            "structuring": 40,
            "validating": 60,
            "highlighting": 80,
            "storing": 90,
            "completed": 100,
            "failed": 0
        }
        
        progress = progress_map.get(result.status.value, 0)
        
        return StatusResponse(
            transaction_id=transaction_id,
            status=result.status,
            progress=progress,
            message=result.processing_log[-1] if result.processing_log else None,
            error=result.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/result/{transaction_id}", response_model=ProcessingResult)
async def get_processing_result(transaction_id: str):
    """Get complete processing result"""
    try:
        result = await storage.get_result(transaction_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Result retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/grounding/{chunk_id}")
async def get_visual_grounding(chunk_id: str, transaction_id: str):
    """Get visual grounding data for a specific chunk"""
    try:
        result = await storage.get_result(transaction_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Find the element
        element = None
        for elem in result.extracted_elements:
            if elem.id == chunk_id:
                element = elem
                break
        
        if not element:
            raise HTTPException(status_code=404, detail="Element not found")
        
        # Get original file path
        file_path = None
        for filename in os.listdir(UPLOAD_DIR):
            if filename.startswith(transaction_id):
                file_path = os.path.join(UPLOAD_DIR, filename)
                break
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Original file not found")
        
        # Get cropped image
        cropped_image = await processor.crop_element_image(
            file_path, 
            element.grounding.page_number, 
            element.grounding.bounding_box
        )
        
        return GroundingResponse(
            chunk_id=chunk_id,
            page_number=element.grounding.page_number,
            bounding_box=element.grounding.bounding_box,
            cropped_image_base64=cropped_image,
            context=str(element.content)[:200] if element.content else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Grounding error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/correct/{transaction_id}")
async def submit_corrections(transaction_id: str, corrections: list[CorrectionRequest]):
    """Submit human corrections for extracted elements"""
    try:
        result = await storage.get_result(transaction_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Apply corrections
        corrections_applied = 0
        for correction in corrections:
            for element in result.extracted_elements:
                if element.id == correction.element_id:
                    # Store original content as backup
                    if not element.corrections:
                        element.corrections = {"original_content": element.content}
                    
                    # Apply correction
                    element.content = correction.corrected_content
                    if correction.corrected_type:
                        element.type = correction.corrected_type
                    
                    # Update metadata
                    element.corrections.update({
                        "corrected_at": datetime.utcnow().isoformat(),
                        "notes": correction.notes
                    })
                    element.validated = True
                    corrections_applied += 1
                    break
        
        # Update processing log
        result.processing_log.append(
            f"Applied {corrections_applied} corrections at {datetime.utcnow()}"
        )
        result.updated_at = datetime.utcnow()
        
        # Save updated result
        await storage.store_result(result)
        
        return JSONResponse(
            content={
                "message": f"Applied {corrections_applied} corrections",
                "transaction_id": transaction_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Correction error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/page-image/{transaction_id}")
async def get_page_image(transaction_id: str, page_number: int = 1):
    """Get base64 encoded image of a document page"""
    try:
        # Find original file
        file_path = None
        for filename in os.listdir(UPLOAD_DIR):
            if filename.startswith(transaction_id):
                file_path = os.path.join(UPLOAD_DIR, filename)
                break
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Original file not found")
        
        # Get page image
        page_image = await processor.get_page_image(file_path, page_number)
        
        if not page_image:
            raise HTTPException(status_code=404, detail="Page not found")
        
        return JSONResponse(content={"image_base64": page_image})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Page image error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/result/{transaction_id}")
async def delete_result(transaction_id: str):
    """Delete processing result and associated files"""
    try:
        # Delete from storage
        deleted = await storage.delete_result(transaction_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Delete uploaded file
        for filename in os.listdir(UPLOAD_DIR):
            if filename.startswith(transaction_id):
                file_path = os.path.join(UPLOAD_DIR, filename)
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted file: {filename}")
                except OSError as e:
                    logger.warning(f"Could not delete file {filename}: {e}")
        
        return JSONResponse(content={"message": "Result deleted successfully"})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(content={"status": "healthy", "timestamp": datetime.utcnow().isoformat()})
