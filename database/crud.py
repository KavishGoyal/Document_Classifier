"""
CRUD (Create, Read, Update, Delete) operations for database
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import Document, ProcessingStatus, ProcessingBatch, AgentLog, DocumentDomain


# Document CRUD Operations

def create_document(
    db: Session,
    filename: str,
    original_path: str,
    file_size: int,
    page_count: Optional[int] = None
) -> Document:
    """Create a new document record"""
    doc = Document(
        filename=filename,
        original_path=original_path,
        file_size=file_size,
        page_count=page_count,
        status=ProcessingStatus.PENDING
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_document(db: Session, document_id: int) -> Optional[Document]:
    """Get document by ID"""
    return db.query(Document).filter(Document.id == document_id).first()


def get_documents(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    domain: Optional[str] = None
) -> List[Document]:
    """Get list of documents with optional filters"""
    query = db.query(Document)
    
    if status:
        try:
            status_enum = ProcessingStatus(status)
            query = query.filter(Document.status == status_enum)
        except ValueError:
            pass
    
    if domain:
        try:
            domain_enum = DocumentDomain(domain)
            query = query.filter(Document.predicted_domain == domain_enum)
        except ValueError:
            pass
    
    return query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()


def count_documents(
    db: Session,
    status: Optional[str] = None,
    domain: Optional[str] = None
) -> int:
    """Count documents with optional filters"""
    query = db.query(Document)
    
    if status:
        try:
            status_enum = ProcessingStatus(status)
            query = query.filter(Document.status == status_enum)
        except ValueError:
            pass
    
    if domain:
        try:
            domain_enum = DocumentDomain(domain)
            query = query.filter(Document.predicted_domain == domain_enum)
        except ValueError:
            pass
    
    return query.count()


def update_document_status(
    db: Session,
    document_id: int,
    status: ProcessingStatus,
    error_message: Optional[str] = None
) -> Optional[Document]:
    """Update document status"""
    doc = get_document(db, document_id)
    
    if doc:
        doc.status = status
        doc.updated_at = datetime.now()
        
        if status == ProcessingStatus.PROCESSING:
            doc.processing_started_at = datetime.now()
        elif status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
            doc.processing_completed_at = datetime.now()
        
        if error_message:
            doc.error_message = error_message
        
        db.commit()
        db.refresh(doc)
    
    return doc


def update_document_classification(
    db: Session,
    document_id: int,
    domain: str,
    confidence: float,
    output_path: Optional[str] = None,
    final_decision: Optional[Dict] = None,
    vision_analysis: Optional[Dict] = None,
    text_analysis: Optional[Dict] = None
) -> Optional[Document]:
    """Update document with classification results"""
    doc = get_document(db, document_id)
    
    if doc:
        try:
            doc.predicted_domain = DocumentDomain(domain)
        except ValueError:
            doc.predicted_domain = DocumentDomain.GENERAL
        
        doc.confidence_score = confidence
        doc.output_path = output_path
        doc.final_decision = final_decision
        doc.vision_analysis = vision_analysis
        doc.text_analysis = text_analysis
        doc.updated_at = datetime.now()
        
        db.commit()
        db.refresh(doc)
    
    return doc


def delete_document(db: Session, document_id: int) -> bool:
    """Delete a document"""
    doc = get_document(db, document_id)
    
    if doc:
        db.delete(doc)
        db.commit()
        return True
    
    return False


# Batch CRUD Operations

def create_batch(
    db: Session,
    batch_name: str,
    total_documents: int
) -> ProcessingBatch:
    """Create a new batch record"""
    batch = ProcessingBatch(
        batch_name=batch_name,
        total_documents=total_documents,
        status=ProcessingStatus.PENDING
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def get_batch(db: Session, batch_id: int) -> Optional[ProcessingBatch]:
    """Get batch by ID"""
    return db.query(ProcessingBatch).filter(ProcessingBatch.id == batch_id).first()


def get_batches(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None
) -> List[ProcessingBatch]:
    """Get list of batches"""
    query = db.query(ProcessingBatch)
    
    if status:
        try:
            status_enum = ProcessingStatus(status)
            query = query.filter(ProcessingBatch.status == status_enum)
        except ValueError:
            pass
    
    return query.order_by(ProcessingBatch.created_at.desc()).offset(skip).limit(limit).all()


def count_batches(db: Session, status: Optional[str] = None) -> int:
    """Count batches"""
    query = db.query(ProcessingBatch)
    
    if status:
        try:
            status_enum = ProcessingStatus(status)
            query = query.filter(ProcessingBatch.status == status_enum)
        except ValueError:
            pass
    
    return query.count()


def update_batch_status(
    db: Session,
    batch_id: int,
    status: ProcessingStatus,
    processed: Optional[int] = None,
    failed: Optional[int] = None,
    domain_distribution: Optional[Dict] = None
) -> Optional[ProcessingBatch]:
    """Update batch status"""
    batch = get_batch(db, batch_id)
    
    if batch:
        batch.status = status
        
        if processed is not None:
            batch.processed_documents = processed
        
        if failed is not None:
            batch.failed_documents = failed
        
        if domain_distribution is not None:
            batch.domain_distribution = domain_distribution
        
        if status == ProcessingStatus.COMPLETED:
            batch.completed_at = datetime.now()
        
        db.commit()
        db.refresh(batch)
    
    return batch


def delete_batch(db: Session, batch_id: int) -> bool:
    """Delete a batch"""
    batch = get_batch(db, batch_id)
    
    if batch:
        db.delete(batch)
        db.commit()
        return True
    
    return False


# Agent Log CRUD Operations

def create_agent_log(
    db: Session,
    document_id: int,
    agent_name: str,
    agent_type: str,
    input_data: Dict,
    output_data: Dict,
    execution_time: float,
    success: bool = True,
    error_message: Optional[str] = None
) -> AgentLog:
    """Create an agent log entry"""
    log = AgentLog(
        document_id=document_id,
        agent_name=agent_name,
        agent_type=agent_type,
        input_data=input_data,
        output_data=output_data,
        execution_time=execution_time,
        success=success,
        error_message=error_message
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_agent_logs(
    db: Session,
    document_id: Optional[int] = None,
    agent_name: Optional[str] = None,
    limit: int = 100
) -> List[AgentLog]:
    """Get agent logs with optional filters"""
    query = db.query(AgentLog)
    
    if document_id:
        query = query.filter(AgentLog.document_id == document_id)
    
    if agent_name:
        query = query.filter(AgentLog.agent_name == agent_name)
    
    return query.order_by(AgentLog.created_at.desc()).limit(limit).all()


# Utility Functions

def get_statistics(db: Session) -> Dict[str, Any]:
    """Get overall statistics"""
    from sqlalchemy import func
    
    total = db.query(Document).count()
    completed = db.query(Document).filter(
        Document.status == ProcessingStatus.COMPLETED
    ).count()
    failed = db.query(Document).filter(
        Document.status == ProcessingStatus.FAILED
    ).count()
    
    # Domain distribution
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
        "total_documents": total,
        "completed": completed,
        "failed": failed,
        "success_rate": (completed / total * 100) if total > 0 else 0,
        "domain_distribution": domain_distribution
    }