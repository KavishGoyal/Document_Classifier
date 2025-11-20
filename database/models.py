from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, Boolean, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentDomain(str, enum.Enum):
    FINANCE = "finance"
    LAW = "law"
    SCIENCE = "science"
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    BUSINESS = "business"
    ENGINEERING = "engineering"
    ARTS = "arts"
    GENERAL = "general"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(500), nullable=False, index=True)
    original_path = Column(String(1000), nullable=False)
    file_size = Column(Integer)
    page_count = Column(Integer)
    
    # Classification results
    predicted_domain = Column(SQLEnum(DocumentDomain), index=True)
    confidence_score = Column(Float)
    
    # Processing status
    status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING, index=True)
    
    # Agent analysis results
    vision_analysis = Column(JSON)  # From Vision Agent
    text_analysis = Column(JSON)    # From Text Classification Agent
    final_decision = Column(JSON)   # From Domain Router Agent
    
    # Output information
    output_path = Column(String(1000))
    output_folder = Column(String(500))
    
    # Metadata
    extracted_text_preview = Column(Text)
    keywords = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processing_started_at = Column(DateTime(timezone=True))
    processing_completed_at = Column(DateTime(timezone=True))
    
    # Error tracking
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', domain={self.predicted_domain})>"


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, index=True)
    agent_name = Column(String(100), index=True)
    agent_type = Column(String(50))
    
    # Agent execution details
    input_data = Column(JSON)
    output_data = Column(JSON)
    execution_time = Column(Float)  # in seconds
    
    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<AgentLog(id={self.id}, agent={self.agent_name}, document_id={self.document_id})>"


class ProcessingBatch(Base):
    __tablename__ = "processing_batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_name = Column(String(200))
    total_documents = Column(Integer)
    processed_documents = Column(Integer, default=0)
    failed_documents = Column(Integer, default=0)
    
    status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING, index=True)
    
    # Statistics
    average_processing_time = Column(Float)
    domain_distribution = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<ProcessingBatch(id={self.id}, name='{self.batch_name}', status={self.status})>"