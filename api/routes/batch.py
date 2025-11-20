"""
Batch processing routes
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
from loguru import logger

from database.config import get_db
from database import crud
from database.models import ProcessingStatus
from tasks.celery_app import process_batch_task

router = APIRouter(prefix="/batch", tags=["batch"])


class BatchProcessRequest(BaseModel):
    folder_path: str
    batch_name: Optional[str] = None
    file_patterns: List[str] = ["*.pdf"]


class BatchStatusResponse(BaseModel):
    id: int
    batch_name: str
    status: str
    total_documents: int
    processed_documents: int
    failed_documents: int
    created_at: str
    completed_at: Optional[str]


@router.post("/process")
async def process_batch(
    request: BatchProcessRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Process multiple documents from a folder"""
    try:
        folder = Path(request.folder_path)
        
        if not folder.exists():
            raise HTTPException(status_code=404, detail="Folder not found")
        
        # Get all PDF files
        pdf_files = []
        for pattern in request.file_patterns:
            pdf_files.extend(list(folder.glob(pattern)))
        
        if not pdf_files:
            raise HTTPException(
                status_code=404, 
                detail=f"No files found matching patterns: {request.file_patterns}"
            )
        
        # Create batch record
        batch_name = request.batch_name or f"Batch_{len(pdf_files)}_docs"
        batch = crud.create_batch(
            db=db,
            batch_name=batch_name,
            total_documents=len(pdf_files)
        )
        
        # Queue batch for processing
        task = process_batch_task.delay(batch.id, [str(f) for f in pdf_files])
        
        logger.info(f"Batch {batch.id} queued with {len(pdf_files)} documents")
        
        return {
            "success": True,
            "batch_id": batch.id,
            "batch_name": batch_name,
            "total_documents": len(pdf_files),
            "task_id": task.id,
            "message": "Batch queued for processing"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch process error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{batch_id}", response_model=BatchStatusResponse)
async def get_batch_status(batch_id: int, db: Session = Depends(get_db)):
    """Get batch processing status"""
    batch = crud.get_batch(db, batch_id)
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    return BatchStatusResponse(
        id=batch.id,
        batch_name=batch.batch_name,
        status=batch.status.value,
        total_documents=batch.total_documents,
        processed_documents=batch.processed_documents or 0,
        failed_documents=batch.failed_documents or 0,
        created_at=batch.created_at.isoformat(),
        completed_at=batch.completed_at.isoformat() if batch.completed_at else None
    )


@router.get("/")
async def list_batches(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all batches with optional status filter"""
    batches = crud.get_batches(db=db, skip=skip, limit=limit, status=status)
    total = crud.count_batches(db, status=status)
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "batches": [
            {
                "id": batch.id,
                "batch_name": batch.batch_name,
                "status": batch.status.value,
                "total_documents": batch.total_documents,
                "processed": batch.processed_documents or 0,
                "failed": batch.failed_documents or 0,
                "created_at": batch.created_at.isoformat(),
                "domain_distribution": batch.domain_distribution
            }
            for batch in batches
        ]
    }


@router.delete("/{batch_id}")
async def delete_batch(batch_id: int, db: Session = Depends(get_db)):
    """Delete a batch record"""
    batch = crud.get_batch(db, batch_id)
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    crud.delete_batch(db, batch_id)
    
    return {
        "success": True,
        "message": f"Batch {batch_id} deleted"
    }


@router.get("/{batch_id}/documents")
async def get_batch_documents(
    batch_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all documents in a batch"""
    batch = crud.get_batch(db, batch_id)
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # This would require adding batch_id to Document model
    # For now, return documents by creation time range
    documents = crud.get_documents(db=db, skip=skip, limit=limit)
    
    return {
        "batch_id": batch_id,
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "status": doc.status.value,
                "domain": doc.predicted_domain.value if doc.predicted_domain else None,
                "confidence": doc.confidence_score
            }
            for doc in documents
        ]
    }