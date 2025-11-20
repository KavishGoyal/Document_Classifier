# """
# FastAPI Application for Document Classification System
# """

# from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Depends
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel
# from typing import List, Optional, Dict, Any
# import os
# from pathlib import Path
# from loguru import logger
# from sqlalchemy.orm import Session

# from database.config import init_db, get_db
# from database.models import Document, ProcessingStatus, ProcessingBatch, AgentLog
# from workflow.graph import workflow
# from config.settings import settings, setup_directories
# from tasks.celery_app import process_document_task, process_batch_task

# # Initialize
# init_db()
# setup_directories()

# app = FastAPI(
#     title="Document Classification System",
#     description="Multi-Agent AI System for Intelligent Document Classification",
#     version="1.0.0"
# )

# # CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # Pydantic models
# class ProcessDocumentRequest(BaseModel):
#     file_path: str


# class ProcessDocumentResponse(BaseModel):
#     success: bool
#     document_id: Optional[int] = None
#     message: str
#     task_id: Optional[str] = None


# class DocumentStatusResponse(BaseModel):
#     id: int
#     filename: str
#     status: str
#     predicted_domain: Optional[str]
#     confidence_score: Optional[float]
#     output_path: Optional[str]
#     created_at: str
#     processing_completed_at: Optional[str]


# class BatchProcessRequest(BaseModel):
#     folder_path: str
#     batch_name: Optional[str] = None


# # Health check
# @app.get("/")
# async def root():
#     return {
#         "service": "Document Classification System",
#         "status": "running",
#         "version": "1.0.0"
#     }


# @app.get("/health")
# async def health_check():
#     """Health check endpoint"""
#     return {
#         "status": "healthy",
#         "database": "connected",
#         "mcp_server": "active"
#     }


# # Document upload
# @app.post("/api/upload")
# async def upload_document(
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db)
# ):
#     """Upload a document for processing"""
#     try:
#         # Save file to input folder
#         file_path = os.path.join(settings.input_folder, file.filename)
        
#         with open(file_path, "wb") as f:
#             content = await file.read()
#             f.write(content)
        
#         logger.info(f"File uploaded: {file.filename}")
        
#         # Create database record
#         doc = Document(
#             filename=file.filename,
#             original_path=file_path,
#             file_size=len(content),
#             status=ProcessingStatus.PENDING
#         )
#         db.add(doc)
#         db.commit()
#         db.refresh(doc)
        
#         return {
#             "success": True,
#             "document_id": doc.id,
#             "filename": file.filename,
#             "message": "File uploaded successfully"
#         }
#     except Exception as e:
#         logger.error(f"Upload error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# # Process single document
# @app.post("/api/process", response_model=ProcessDocumentResponse)
# async def process_document(
#     request: ProcessDocumentRequest,
#     background_tasks: BackgroundTasks,
#     db: Session = Depends(get_db)
# ):
#     """Process a single document"""
#     try:
#         file_path = request.file_path
        
#         if not os.path.exists(file_path):
#             raise HTTPException(status_code=404, detail="File not found")
        
#         # Create database record
#         doc = Document(
#             filename=os.path.basename(file_path),
#             original_path=file_path,
#             file_size=os.path.getsize(file_path),
#             status=ProcessingStatus.PENDING
#         )
#         db.add(doc)
#         db.commit()
#         db.refresh(doc)
        
#         # Queue for background processing
#         task = process_document_task.delay(doc.id)
        
#         return ProcessDocumentResponse(
#             success=True,
#             document_id=doc.id,
#             message="Document queued for processing",
#             task_id=task.id
#         )
#     except Exception as e:
#         logger.error(f"Process document error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# # Process synchronously (for testing/demo)
# @app.post("/api/process-sync")
# async def process_document_sync(
#     request: ProcessDocumentRequest,
#     db: Session = Depends(get_db)
# ):
#     """Process document synchronously"""
#     try:
#         file_path = request.file_path
        
#         if not os.path.exists(file_path):
#             raise HTTPException(status_code=404, detail="File not found")
        
#         # Create database record
#         doc = Document(
#             filename=os.path.basename(file_path),
#             original_path=file_path,
#             file_size=os.path.getsize(file_path),
#             status=ProcessingStatus.PROCESSING
#         )
#         db.add(doc)
#         db.commit()
#         db.refresh(doc)
        
#         # Process immediately
#         result = await workflow.process_document(file_path)
        
#         # Update database
#         doc.status = ProcessingStatus.COMPLETED if result["success"] else ProcessingStatus.FAILED
#         doc.predicted_domain = result.get("domain")
#         doc.confidence_score = result.get("confidence")
#         doc.output_path = result.get("output_path")
#         doc.final_decision = result.get("final_decision")
        
#         db.commit()
        
#         return {
#             "success": result["success"],
#             "document_id": doc.id,
#             "filename": result.get("filename"),
#             "domain": result.get("domain"),
#             "confidence": result.get("confidence"),
#             "output_path": result.get("output_path")
#         }
#     except Exception as e:
#         logger.error(f"Sync process error: {e}")
#         if doc:
#             doc.status = ProcessingStatus.FAILED
#             doc.error_message = str(e)
#             db.commit()
#         raise HTTPException(status_code=500, detail=str(e))


# # Process batch
# @app.post("/api/batch-process")
# async def batch_process(
#     request: BatchProcessRequest,
#     background_tasks: BackgroundTasks,
#     db: Session = Depends(get_db)
# ):
#     """Process multiple documents from a folder"""
#     try:
#         folder_path = request.folder_path
        
#         if not os.path.exists(folder_path):
#             raise HTTPException(status_code=404, detail="Folder not found")
        
#         # Get all PDF files
#         pdf_files = list(Path(folder_path).glob("*.pdf"))
        
#         if not pdf_files:
#             raise HTTPException(status_code=404, detail="No PDF files found in folder")
        
#         # Create batch record
#         batch = ProcessingBatch(
#             batch_name=request.batch_name or f"Batch_{len(pdf_files)}_docs",
#             total_documents=len(pdf_files),
#             status=ProcessingStatus.PENDING
#         )
#         db.add(batch)
#         db.commit()
#         db.refresh(batch)
        
#         # Queue batch for processing
#         task = process_batch_task.delay(batch.id, [str(f) for f in pdf_files])
        
#         return {
#             "success": True,
#             "batch_id": batch.id,
#             "total_documents": len(pdf_files),
#             "message": "Batch queued for processing",
#             "task_id": task.id
#         }
#     except Exception as e:
#         logger.error(f"Batch process error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# # Get document status
# @app.get("/api/documents/{document_id}", response_model=DocumentStatusResponse)
# async def get_document_status(document_id: int, db: Session = Depends(get_db)):
#     """Get document processing status"""
#     doc = db.query(Document).filter(Document.id == document_id).first()
    
#     if not doc:
#         raise HTTPException(status_code=404, detail="Document not found")
    
#     return DocumentStatusResponse(
#         id=doc.id,
#         filename=doc.filename,
#         status=doc.status.value,
#         predicted_domain=doc.predicted_domain.value if doc.predicted_domain else None,
#         confidence_score=doc.confidence_score,
#         output_path=doc.output_path,
#         created_at=doc.created_at.isoformat(),
#         processing_completed_at=doc.processing_completed_at.isoformat() if doc.processing_completed_at else None
#     )


# # List documents
# @app.get("/api/documents")
# async def list_documents(
#     skip: int = 0,
#     limit: int = 50,
#     status: Optional[str] = None,
#     domain: Optional[str] = None,
#     db: Session = Depends(get_db)
# ):
#     """List all documents with optional filters"""
#     query = db.query(Document)
    
#     if status:
#         query = query.filter(Document.status == status)
#     if domain:
#         query = query.filter(Document.predicted_domain == domain)
    
#     total = query.count()
#     documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    
#     return {
#         "total": total,
#         "documents": [
#             {
#                 "id": doc.id,
#                 "filename": doc.filename,
#                 "status": doc.status.value,
#                 "domain": doc.predicted_domain.value if doc.predicted_domain else None,
#                 "confidence": doc.confidence_score,
#                 "created_at": doc.created_at.isoformat()
#             }
#             for doc in documents
#         ]
#     }


# # Statistics
# @app.get("/api/statistics")
# async def get_statistics(db: Session = Depends(get_db)):
#     """Get processing statistics"""
#     total_docs = db.query(Document).count()
#     completed = db.query(Document).filter(Document.status == ProcessingStatus.COMPLETED).count()
#     pending = db.query(Document).filter(Document.status == ProcessingStatus.PENDING).count()
#     failed = db.query(Document).filter(Document.status == ProcessingStatus.FAILED).count()
    
#     # Domain distribution
#     from sqlalchemy import func
#     domain_stats = db.query(
#         Document.predicted_domain,
#         func.count(Document.id)
#     ).filter(
#         Document.predicted_domain.isnot(None)
#     ).group_by(Document.predicted_domain).all()
    
#     domain_distribution = {
#         domain.value: count for domain, count in domain_stats if domain
#     }
    
#     return {
#         "total_documents": total_docs,
#         "completed": completed,
#         "pending": pending,
#         "failed": failed,
#         "domain_distribution": domain_distribution
#     }


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host=settings.api_host, port=settings.api_port)

"""
FastAPI Application for Document Classification System
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from pathlib import Path
from loguru import logger
from sqlalchemy.orm import Session

from database.config import init_db, get_db
from database.models import Document, ProcessingStatus, ProcessingBatch, AgentLog
from workflow.graph import workflow
from config.settings import settings, setup_directories
from tasks.celery_app import process_document_task, process_batch_task

# Initialize
init_db()
setup_directories()

app = FastAPI(
    title="Document Classification System",
    description="Multi-Agent AI System for Intelligent Document Classification",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class ProcessDocumentRequest(BaseModel):
    file_path: str


class ProcessDocumentResponse(BaseModel):
    success: bool
    document_id: Optional[int] = None
    message: str
    task_id: Optional[str] = None


class DocumentStatusResponse(BaseModel):
    id: int
    filename: str
    status: str
    predicted_domain: Optional[str]
    confidence_score: Optional[float]
    output_path: Optional[str]
    created_at: str
    processing_completed_at: Optional[str]


class BatchProcessRequest(BaseModel):
    folder_path: str
    batch_name: Optional[str] = None


# Include API routes
from api.routes import api_router
app.include_router(api_router, prefix="/api")


# Health check
@app.get("/")
async def root():
    return {
        "service": "Document Classification System",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "mcp_server": "active"
    }


# Document upload
@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a document for processing"""
    try:
        # Save file to input folder
        file_path = os.path.join(settings.input_folder, file.filename)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"File uploaded: {file.filename}")
        
        # Create database record
        doc = Document(
            filename=file.filename,
            original_path=file_path,
            file_size=len(content),
            status=ProcessingStatus.PENDING
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        return {
            "success": True,
            "document_id": doc.id,
            "filename": file.filename,
            "message": "File uploaded successfully"
        }
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Process single document
@app.post("/api/process", response_model=ProcessDocumentResponse)
async def process_document(
    request: ProcessDocumentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Process a single document"""
    try:
        file_path = request.file_path
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Create database record
        doc = Document(
            filename=os.path.basename(file_path),
            original_path=file_path,
            file_size=os.path.getsize(file_path),
            status=ProcessingStatus.PENDING
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # Queue for background processing
        task = process_document_task.delay(doc.id)
        
        return ProcessDocumentResponse(
            success=True,
            document_id=doc.id,
            message="Document queued for processing",
            task_id=task.id
        )
    except Exception as e:
        logger.error(f"Process document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Process synchronously (for testing/demo)
@app.post("/api/process-sync")
async def process_document_sync(
    request: ProcessDocumentRequest,
    db: Session = Depends(get_db)
):
    """Process document synchronously"""
    try:
        file_path = request.file_path
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Create database record
        doc = Document(
            filename=os.path.basename(file_path),
            original_path=file_path,
            file_size=os.path.getsize(file_path),
            status=ProcessingStatus.PROCESSING
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # Process immediately
        result = await workflow.process_document(file_path)
        
        # Update database
        doc.status = ProcessingStatus.COMPLETED if result["success"] else ProcessingStatus.FAILED
        doc.predicted_domain = result.get("domain")
        doc.confidence_score = result.get("confidence")
        doc.output_path = result.get("output_path")
        doc.final_decision = result.get("final_decision")
        
        db.commit()
        
        return {
            "success": result["success"],
            "document_id": doc.id,
            "filename": result.get("filename"),
            "domain": result.get("domain"),
            "confidence": result.get("confidence"),
            "output_path": result.get("output_path")
        }
    except Exception as e:
        logger.error(f"Sync process error: {e}")
        if doc:
            doc.status = ProcessingStatus.FAILED
            doc.error_message = str(e)
            db.commit()
        raise HTTPException(status_code=500, detail=str(e))


# Process batch
@app.post("/api/batch-process")
async def batch_process(
    request: BatchProcessRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Process multiple documents from a folder"""
    try:
        folder_path = request.folder_path
        
        if not os.path.exists(folder_path):
            raise HTTPException(status_code=404, detail="Folder not found")
        
        # Get all PDF files
        pdf_files = list(Path(folder_path).glob("*.pdf"))
        
        if not pdf_files:
            raise HTTPException(status_code=404, detail="No PDF files found in folder")
        
        # Create batch record
        batch = ProcessingBatch(
            batch_name=request.batch_name or f"Batch_{len(pdf_files)}_docs",
            total_documents=len(pdf_files),
            status=ProcessingStatus.PENDING
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        
        # Queue batch for processing
        task = process_batch_task.delay(batch.id, [str(f) for f in pdf_files])
        
        return {
            "success": True,
            "batch_id": batch.id,
            "total_documents": len(pdf_files),
            "message": "Batch queued for processing",
            "task_id": task.id
        }
    except Exception as e:
        logger.error(f"Batch process error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Get document status
@app.get("/api/documents/{document_id}", response_model=DocumentStatusResponse)
async def get_document_status(document_id: int, db: Session = Depends(get_db)):
    """Get document processing status"""
    doc = db.query(Document).filter(Document.id == document_id).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentStatusResponse(
        id=doc.id,
        filename=doc.filename,
        status=doc.status.value,
        predicted_domain=doc.predicted_domain.value if doc.predicted_domain else None,
        confidence_score=doc.confidence_score,
        output_path=doc.output_path,
        created_at=doc.created_at.isoformat(),
        processing_completed_at=doc.processing_completed_at.isoformat() if doc.processing_completed_at else None
    )


# List documents
@app.get("/api/documents")
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    domain: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all documents with optional filters"""
    query = db.query(Document)
    
    if status:
        query = query.filter(Document.status == status)
    if domain:
        query = query.filter(Document.predicted_domain == domain)
    
    total = query.count()
    documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
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


# Statistics
@app.get("/api/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Get processing statistics"""
    total_docs = db.query(Document).count()
    completed = db.query(Document).filter(Document.status == ProcessingStatus.COMPLETED).count()
    pending = db.query(Document).filter(Document.status == ProcessingStatus.PENDING).count()
    failed = db.query(Document).filter(Document.status == ProcessingStatus.FAILED).count()
    
    # Domain distribution
    from sqlalchemy import func
    domain_stats = db.query(
        Document.predicted_domain,
        func.count(Document.id)
    ).filter(
        Document.predicted_domain.isnot(None)
    ).group_by(Document.predicted_domain).all()
    
    domain_distribution = {
        domain.value: count for domain, count in domain_stats if domain
    }
    
    return {
        "total_documents": total_docs,
        "completed": completed,
        "pending": pending,
        "failed": failed,
        "domain_distribution": domain_distribution
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)