"""
Statistics and analytics routes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional

from database.config import get_db
from database.models import Document, ProcessingStatus, DocumentDomain, AgentLog
from mcp.client import mcp_client

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/overview")
async def get_statistics_overview(db: Session = Depends(get_db)):
    """Get overall statistics"""
    total_docs = db.query(Document).count()
    completed = db.query(Document).filter(
        Document.status == ProcessingStatus.COMPLETED
    ).count()
    pending = db.query(Document).filter(
        Document.status == ProcessingStatus.PENDING
    ).count()
    processing = db.query(Document).filter(
        Document.status == ProcessingStatus.PROCESSING
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
    
    # Average confidence
    avg_confidence = db.query(
        func.avg(Document.confidence_score)
    ).filter(
        Document.confidence_score.isnot(None)
    ).scalar() or 0.0
    
    return {
        "total_documents": total_docs,
        "completed": completed,
        "pending": pending,
        "processing": processing,
        "failed": failed,
        "success_rate": (completed / total_docs * 100) if total_docs > 0 else 0,
        "domain_distribution": domain_distribution,
        "average_confidence": round(avg_confidence, 4)
    }


@router.get("/domain/{domain}")
async def get_domain_statistics(domain: str, db: Session = Depends(get_db)):
    """Get statistics for a specific domain"""
    try:
        domain_enum = DocumentDomain(domain)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid domain: {domain}")
    
    docs = db.query(Document).filter(
        Document.predicted_domain == domain_enum
    ).all()
    
    if not docs:
        return {
            "domain": domain,
            "document_count": 0,
            "average_confidence": 0,
            "total_size_mb": 0
        }
    
    total_size = sum(doc.file_size or 0 for doc in docs)
    avg_confidence = sum(doc.confidence_score or 0 for doc in docs) / len(docs)
    
    return {
        "domain": domain,
        "document_count": len(docs),
        "average_confidence": round(avg_confidence, 4),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "confidence": doc.confidence_score
            }
            for doc in docs[:10]  # Return first 10 as sample
        ]
    }


@router.get("/timeline")
async def get_processing_timeline(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get processing timeline for the last N days"""
    start_date = datetime.now() - timedelta(days=days)
    
    docs = db.query(
        func.date(Document.created_at).label('date'),
        func.count(Document.id).label('count'),
        Document.status
    ).filter(
        Document.created_at >= start_date
    ).group_by(
        func.date(Document.created_at),
        Document.status
    ).all()
    
    # Organize by date
    timeline = {}
    for date, count, status in docs:
        date_str = str(date)
        if date_str not in timeline:
            timeline[date_str] = {
                "date": date_str,
                "completed": 0,
                "failed": 0,
                "pending": 0,
                "processing": 0
            }
        timeline[date_str][status.value] = count
    
    return {
        "period_days": days,
        "timeline": list(timeline.values())
    }


@router.get("/confidence-distribution")
async def get_confidence_distribution(db: Session = Depends(get_db)):
    """Get confidence score distribution"""
    docs = db.query(Document.confidence_score).filter(
        Document.confidence_score.isnot(None)
    ).all()
    
    if not docs:
        return {
            "total_documents": 0,
            "distribution": {}
        }
    
    # Create bins
    bins = {
        "0.0-0.2": 0,
        "0.2-0.4": 0,
        "0.4-0.6": 0,
        "0.6-0.8": 0,
        "0.8-1.0": 0
    }
    
    for (score,) in docs:
        if score < 0.2:
            bins["0.0-0.2"] += 1
        elif score < 0.4:
            bins["0.2-0.4"] += 1
        elif score < 0.6:
            bins["0.4-0.6"] += 1
        elif score < 0.8:
            bins["0.6-0.8"] += 1
        else:
            bins["0.8-1.0"] += 1
    
    return {
        "total_documents": len(docs),
        "distribution": bins
    }


@router.get("/agent-performance")
async def get_agent_performance(db: Session = Depends(get_db)):
    """Get agent performance statistics"""
    agent_stats = db.query(
        AgentLog.agent_name,
        func.count(AgentLog.id).label('total_runs'),
        func.avg(AgentLog.execution_time).label('avg_time'),
        func.sum(func.cast(AgentLog.success, Integer)).label('successes')
    ).group_by(AgentLog.agent_name).all()
    
    return {
        "agents": [
            {
                "name": name,
                "total_runs": total,
                "average_execution_time": round(avg_time, 4) if avg_time else 0,
                "success_rate": (successes / total * 100) if total > 0 else 0
            }
            for name, total, avg_time, successes in agent_stats
        ]
    }


@router.get("/file-system")
async def get_file_system_statistics():
    """Get file system statistics from MCP server"""
    try:
        stats = await mcp_client.get_statistics()
        
        if stats.get("success"):
            return {
                "success": True,
                "statistics": stats.get("statistics", {}),
                "total_files": stats.get("total_files", 0)
            }
        else:
            return {
                "success": False,
                "error": stats.get("message", "Failed to get statistics")
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/performance-metrics")
async def get_performance_metrics(db: Session = Depends(get_db)):
    """Get system performance metrics"""
    # Get processing times
    completed_docs = db.query(
        Document.processing_started_at,
        Document.processing_completed_at
    ).filter(
        Document.processing_started_at.isnot(None),
        Document.processing_completed_at.isnot(None)
    ).all()
    
    if not completed_docs:
        return {
            "total_processed": 0,
            "average_processing_time": 0,
            "min_processing_time": 0,
            "max_processing_time": 0
        }
    
    processing_times = [
        (completed - started).total_seconds()
        for started, completed in completed_docs
        if started and completed
    ]
    
    return {
        "total_processed": len(processing_times),
        "average_processing_time": round(sum(processing_times) / len(processing_times), 2),
        "min_processing_time": round(min(processing_times), 2),
        "max_processing_time": round(max(processing_times), 2),
        "median_processing_time": round(sorted(processing_times)[len(processing_times) // 2], 2)
    }


# Fix missing import
from sqlalchemy import Integer