"""
Document management routes
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from pathlib import Path
from loguru import logger

from database.config import get_db
from database import crud
from database.models import Document, ProcessingStatus
from config.settings import settings
from workflow.graph import workflow
from tasks.celery_app import process_document_task

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a document for processing"""
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Save file to input folder
        file_path = os.path.join(settings.input_folder, file.filename)
        
        # Handle duplicate filenames
        if os.path.exists(file_path):
            base_name = Path(file.filename).stem
            extension = Path(file.filename).suffix
            counter = 1
            while os.path.exists(file_path):
                file_path = os.path.join(
                    settings.input_folder,
                    f"{base_name}_{counter}{extension}"
                )
                counter += 1
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"File uploaded: {file.filename} ({len(content)} bytes)")
        
        # Create database record
        doc = crud.create_document(
            db=db,
            filename=os.path.basename(file_path),
            original_path=file_path,
            file_size=len(content)
        )
        
        return {
            "success": True,
            "document_id": doc.id,
            "filename": os.path.basename(file_path),
            "size": len(content),
            "message": "File uploaded successfully"
        }
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{document_id}/process")
async def process_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Queue a document for processing"""
    doc = crud.get_document(db, document_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if doc.status != ProcessingStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Document already processed or in processing. Status: {doc.status}"
        )
    
    # Queue for background processing
    task = process_document_task.delay(document_id)
    
    return {
        "success": True,
        "document_id": document_id,
        "task_id": task.id,
        "message": "Document queued for processing"
    }


@router.post("/{document_id}/process-sync")
async def process_document_sync(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Process document synchronously (for testing/demo)"""
    doc = crud.get_document(db, document_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Update status
    crud.update_document_status(db, document_id, ProcessingStatus.PROCESSING)
    
    try:
        # Process immediately
        result = await workflow.process_document(doc.original_path)
        
        # Update database with results
        if result["success"]:
            crud.update_document_classification(
                db=db,
                document_id=document_id,
                domain=result.get("domain"),
                confidence=result.get("confidence"),
                output_path=result.get("output_path"),
                final_decision=result.get("final_decision")
            )
            
            crud.update_document_status(db, document_id, ProcessingStatus.COMPLETED)
        else:
            crud.update_document_status(
                db, 
                document_id, 
                ProcessingStatus.FAILED,
                error_message=result.get("error")
            )
        
        return {
            "success": result["success"],
            "document_id": document_id,
            "filename": result.get("filename"),
            "domain": result.get("domain"),
            "confidence": result.get("confidence"),
            "output_path": result.get("output_path")
        }
    except Exception as e:
        logger.error(f"Sync process error: {e}")
        crud.update_document_status(
            db, 
            document_id, 
            ProcessingStatus.FAILED,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}")
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get document details"""
    doc = crud.get_document(db, document_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": doc.id,
        "filename": doc.filename,
        "status": doc.status.value,
        "predicted_domain": doc.predicted_domain.value if doc.predicted_domain else None,
        "confidence_score": doc.confidence_score,
        "output_path": doc.output_path,
        "file_size": doc.file_size,
        "page_count": doc.page_count,
        "created_at": doc.created_at.isoformat(),
        "processing_completed_at": doc.processing_completed_at.isoformat() if doc.processing_completed_at else None,
        "error_message": doc.error_message
    }


@router.get("/")
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    domain: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List documents with optional filters"""
    documents = crud.get_documents(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        domain=domain
    )
    
    total = crud.count_documents(db, status=status, domain=domain)
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "status": doc.status.value,
                "domain": doc.predicted_domain.value if doc.predicted_domain else None,
                "confidence": doc.confidence_score,
                "created_at": doc.created_at.isoformat()
            }
            for doc in documents
        ]
    }


@router.delete("/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a document record"""
    doc = crud.get_document(db, document_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete from database
    crud.delete_document(db, document_id)
    
    return {
        "success": True,
        "message": f"Document {document_id} deleted"
    }


@router.post("/{document_id}/retry")
async def retry_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Retry processing a failed document"""
    doc = crud.get_document(db, document_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Reset status
    crud.update_document_status(db, document_id, ProcessingStatus.PENDING)
    doc.retry_count = (doc.retry_count or 0) + 1
    db.commit()
    
    # Queue for processing
    task = process_document_task.delay(document_id)
    
    return {
        "success": True,
        "document_id": document_id,
        "task_id": task.id,
        "retry_count": doc.retry_count,
        "message": "Document queued for retry"
    }