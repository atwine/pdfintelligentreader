"""
SQLAlchemy models for PDF processing data
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy import create_engine

Base = declarative_base()


class ProcessingSession(Base):
    """Processing session for tracking batch operations"""
    __tablename__ = "processing_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="processing")  # processing, completed, failed
    total_documents = Column(Integer, default=0)
    processed_documents = Column(Integer, default=0)
    total_sentences = Column(Integer, default=0)
    
    # Relationships
    documents = relationship("Document", back_populates="session")


class Document(Base):
    """Document model for storing PDF metadata and processing results"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), ForeignKey("processing_sessions.session_id"))
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # Processing metadata
    extraction_method = Column(String(50))  # pymupdf, pdfplumber, ocr
    processing_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Document analysis
    total_pages = Column(Integer)
    total_sentences = Column(Integer, default=0)
    language_detected = Column(String(10))
    
    # Quality metrics
    avg_completeness_score = Column(Float)
    avg_clarity_score = Column(Float)
    avg_structure_score = Column(Float)
    avg_translation_readiness = Column(Float)
    noise_percentage = Column(Float)
    
    # Relationships
    session = relationship("ProcessingSession", back_populates="documents")
    sentences = relationship("Sentence", back_populates="document", cascade="all, delete-orphan")


class Sentence(Base):
    """Sentence model for storing extracted and processed sentences"""
    __tablename__ = "sentences"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    
    # Content
    original_text = Column(Text, nullable=False)
    processed_text = Column(Text)
    
    # Position and context
    page_number = Column(Integer)
    sentence_index = Column(Integer)
    paragraph_context = Column(Text)
    
    # Processing metadata
    extraction_confidence = Column(Float)
    boundary_confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Quality flags
    is_complete = Column(Boolean, default=True)
    is_translation_ready = Column(Boolean, default=True)
    has_issues = Column(Boolean, default=False)
    issue_description = Column(Text)
    
    # Relationships
    document = relationship("Document", back_populates="sentences")
    quality_scores = relationship("QualityScore", back_populates="sentence", cascade="all, delete-orphan")


class QualityScore(Base):
    """Quality assessment scores for sentences"""
    __tablename__ = "quality_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    sentence_id = Column(Integer, ForeignKey("sentences.id"))
    
    # Quality dimensions
    completeness_score = Column(Float)  # Grammatical completeness
    clarity_score = Column(Float)       # Readability and coherence
    structure_score = Column(Float)     # Proper sentence structure
    content_score = Column(Float)       # Content quality
    translation_readiness = Column(Float)  # Overall translation suitability
    
    # Overall assessment
    overall_score = Column(Float)
    confidence = Column(Float)
    
    # Assessment metadata
    assessed_at = Column(DateTime, default=datetime.utcnow)
    assessment_method = Column(String(50))  # ai, rule_based, hybrid
    
    # Relationships
    sentence = relationship("Sentence", back_populates="quality_scores")


# Database utilities
def create_database(database_url: str) -> None:
    """Create database tables"""
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)


def get_database_session(database_url: str) -> Session:
    """Get database session"""
    engine = create_engine(database_url)
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()
