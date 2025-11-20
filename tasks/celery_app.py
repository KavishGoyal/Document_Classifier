"""
Celery tasks for asynchronous document processing
"""

# from tasks.celery_app import Celery
from celery import Celery
from typing import List
import asyncio
from datetime import datetime
from loguru import logger

from config.settings import settings
from database.config import get_db_context
from database.models import Document, ProcessingStatus, ProcessingBatch, AgentLog, DocumentDomain
from workflow.graph import workflow

# Initialize Celery
celery_app = Celery(
    'document_classifier',
    broker=settings.redis_url,
    backend=settings.redis_url
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


@celery_app.task(name='process_document')
def process_document_task(document_id: int):
    """Process a single document asynchronously"""
    logger.info(f"Starting task for document ID: {document_id}")
    
    try:
        with get_db_context() as db:
            # Get document
            doc = db.query(Document).filter(Document.id == document_id).first()
            
            if not doc:
                logger.error(f"Document {document_id} not found")
                return {"success": False, "error": "Document not found"}
            
            # Update status
            doc.status = ProcessingStatus.PROCESSING
            doc.processing_started_at = datetime.now()
            db.commit()
            
            # Process document using workflow
            result = asyncio.run(workflow.process_document(doc.original_path))
            
            # Update document with results
            if result["success"]:
                doc.status = ProcessingStatus.COMPLETED
                doc.predicted_domain = DocumentDomain(result["domain"])
                doc.confidence_score = result["confidence"]
                doc.output_path = result.get("output_path")
                doc.final_decision = result.get("final_decision")
                doc.processing_completed_at = datetime.now()
                
                logger.info(f"Document {document_id} processed successfully: {result['domain']}")
            else:
                doc.status = ProcessingStatus.FAILED
                doc.error_message = result.get("error", "Unknown error")
                
                logger.error(f"Document {document_id} processing failed: {result.get('error')}")
            
            db.commit()
            
            return {
                "success": result["success"],
                "document_id": document_id,
                "domain": result.get("domain"),
                "confidence": result.get("confidence")
            }
            
    except Exception as e:
        logger.error(f"Task error for document {document_id}: {e}")
        
        with get_db_context() as db:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = ProcessingStatus.FAILED
                doc.error_message = str(e)
                db.commit()
        
        return {"success": False, "error": str(e)}


@celery_app.task(name='process_batch')
def process_batch_task(batch_id: int, file_paths: List[str]):
    """Process multiple documents in batch"""
    logger.info(f"Starting batch task {batch_id} with {len(file_paths)} files")
    
    try:
        with get_db_context() as db:
            batch = db.query(ProcessingBatch).filter(ProcessingBatch.id == batch_id).first()
            
            if not batch:
                logger.error(f"Batch {batch_id} not found")
                return {"success": False, "error": "Batch not found"}
            
            batch.status = ProcessingStatus.PROCESSING
            db.commit()
            
            processed = 0
            failed = 0
            domain_counts = {}
            
            for file_path in file_paths:
                try:
                    # Create document record
                    import os
                    doc = Document(
                        filename=os.path.basename(file_path),
                        original_path=file_path,
                        file_size=os.path.getsize(file_path),
                        status=ProcessingStatus.PROCESSING
                    )
                    db.add(doc)
                    db.commit()
                    db.refresh(doc)
                    
                    # Process document
                    result = asyncio.run(workflow.process_document(file_path))
                    
                    if result["success"]:
                        doc.status = ProcessingStatus.COMPLETED
                        doc.predicted_domain = DocumentDomain(result["domain"])
                        doc.confidence_score = result["confidence"]
                        doc.output_path = result.get("output_path")
                        doc.processing_completed_at = datetime.now()
                        
                        processed += 1
                        domain = result["domain"]
                        domain_counts[domain] = domain_counts.get(domain, 0) + 1
                    else:
                        doc.status = ProcessingStatus.FAILED
                        doc.error_message = result.get("error")
                        failed += 1
                    
                    db.commit()
                    
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    failed += 1
            
            # Update batch
            batch.status = ProcessingStatus.COMPLETED
            batch.processed_documents = processed
            batch.failed_documents = failed
            batch.domain_distribution = domain_counts
            batch.completed_at = datetime.now()
            db.commit()
            
            logger.info(f"Batch {batch_id} completed: {processed} processed, {failed} failed")
            
            return {
                "success": True,
                "batch_id": batch_id,
                "processed": processed,
                "failed": failed,
                "domain_distribution": domain_counts
            }
            
    except Exception as e:
        logger.error(f"Batch task error: {e}")
        
        with get_db_context() as db:
            batch = db.query(ProcessingBatch).filter(ProcessingBatch.id == batch_id).first()
            if batch:
                batch.status = ProcessingStatus.FAILED
                db.commit()
        
        return {"success": False, "error": str(e)}