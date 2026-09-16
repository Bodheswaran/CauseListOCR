"""
Database models for CauseListOCR
Defines SQLAlchemy ORM models for storing extracted data
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ConfidenceLevelEnum(Enum):
    """Confidence level enumeration."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    CRITICAL = "CRITICAL"


class ProcessingStatusEnum(Enum):
    """OCR processing status enumeration."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVIEWED = "REVIEWED"


class CauseListDocument(Base):
    """Represents a scanned cause list document."""
    
    __tablename__ = "cause_list_documents"
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False, unique=True)
    file_size = Column(Integer)  # in bytes
    upload_date = Column(DateTime, default=datetime.utcnow)
    pages = Column(Integer)  # Number of pages in document
    processing_status = Column(SQLEnum(ProcessingStatusEnum), default=ProcessingStatusEnum.PENDING)
    processing_started = Column(DateTime)
    processing_completed = Column(DateTime)
    ocr_engine = Column(String(50))  # e.g., 'Tesseract', 'AWS Textract'
    notes = Column(Text)
    
    # Relationships
    extraction_runs = relationship("ExtractionRun", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CauseListDocument(id={self.id}, filename='{self.filename}', status={self.processing_status})>"


class ExtractionRun(Base):
    """Represents a single extraction run on a document."""
    
    __tablename__ = "extraction_runs"
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("cause_list_documents.id"), nullable=False)
    run_date = Column(DateTime, default=datetime.utcnow)
    extraction_method = Column(String(100))  # e.g., 'line-based', 'table-based'
    total_records_extracted = Column(Integer, default=0)
    duplicates_found = Column(Integer, default=0)
    records_requiring_review = Column(Integer, default=0)
    average_confidence = Column(Float)  # 0.0 to 1.0
    errors_encountered = Column(Text)  # JSON or plain text error log
    
    # Relationships
    document = relationship("CauseListDocument", back_populates="extraction_runs")
    records = relationship("ExtractedRecord", back_populates="extraction_run", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ExtractionRun(id={self.id}, doc_id={self.document_id}, records={self.total_records_extracted})>"


class ExtractedRecord(Base):
    """Represents a single extracted case record."""
    
    __tablename__ = "extracted_records"
    
    id = Column(Integer, primary_key=True)
    extraction_run_id = Column(Integer, ForeignKey("extraction_runs.id"), nullable=False)
    page_number = Column(Integer)  # Page number in document
    line_number = Column(Integer)  # Line number on page
    sequence_number = Column(Integer)  # Sequential order in extraction
    
    # Core fields
    case_number = Column(String(50), nullable=False, index=True)
    hearing_date = Column(String(20))  # DD-MM-YYYY format
    party_name = Column(String(500))
    advocate = Column(String(300))
    
    # Confidence scores
    case_number_confidence = Column(Float, default=0.0)  # 0.0 to 1.0
    date_confidence = Column(Float, default=0.0)
    party_name_confidence = Column(Float, default=0.0)
    advocate_confidence = Column(Float, default=0.0)
    overall_confidence = Column(Float, default=0.0)
    confidence_level = Column(SQLEnum(ConfidenceLevelEnum), default=ConfidenceLevelEnum.MEDIUM)
    
    # Quality flags
    needs_review = Column(Boolean, default=False)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_record_id = Column(Integer, ForeignKey("extracted_records.id"))  # Self-referential for duplicates
    
    # Validation and processing
    validation_passed = Column(Boolean, default=False)
    validation_issues = Column(Text)  # JSON array of issues
    manual_review_notes = Column(Text)
    reviewed_by = Column(String(100))  # Username who reviewed
    review_date = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    extraction_run = relationship("ExtractionRun", back_populates="records")
    
    def __repr__(self):
        return f"<ExtractedRecord(id={self.id}, case_number='{self.case_number}', conf_level={self.confidence_level})>"


class ProcessingLog(Base):
    """Log of all processing activities for audit trail."""
    
    __tablename__ = "processing_logs"
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("cause_list_documents.id"))
    record_id = Column(Integer, ForeignKey("extracted_records.id"))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    activity = Column(String(255))  # e.g., 'OCR_STARTED', 'VALIDATION_FAILED', 'MANUALLY_REVIEWED'
    status = Column(String(50))  # e.g., 'SUCCESS', 'FAILED', 'WARNING'
    details = Column(Text)  # JSON details
    user = Column(String(100))  # Username performing action
    
    def __repr__(self):
        return f"<ProcessingLog(id={self.id}, activity='{self.activity}', status='{self.status}')>"


class ReviewQueue(Base):
    """Queue of records requiring manual review."""
    
    __tablename__ = "review_queue"
    
    id = Column(Integer, primary_key=True)
    record_id = Column(Integer, ForeignKey("extracted_records.id"), nullable=False, unique=True)
    reason = Column(String(255))  # Why it needs review
    priority = Column(Integer, default=0)  # Higher = more urgent
    added_date = Column(DateTime, default=datetime.utcnow)
    assigned_to = Column(String(100))  # Reviewer username
    status = Column(String(50), default="PENDING")  # PENDING, IN_REVIEW, COMPLETED, REJECTED
    completed_date = Column(DateTime)
    reviewer_notes = Column(Text)
    
    def __repr__(self):
        return f"<ReviewQueue(record_id={self.record_id}, reason='{self.reason}', status='{self.status}')>"


class ExportLog(Base):
    """Log of all data exports."""
    
    __tablename__ = "export_logs"
    
    id = Column(Integer, primary_key=True)
    export_date = Column(DateTime, default=datetime.utcnow, index=True)
    format = Column(String(50))  # CSV, JSON, Excel, HTML
    record_count = Column(Integer)
    filters_applied = Column(Text)  # JSON filters
    user = Column(String(100))
    output_file = Column(String(512))  # Path to exported file
    
    def __repr__(self):
        return f"<ExportLog(id={self.id}, format='{self.format}', records={self.record_count})>"
