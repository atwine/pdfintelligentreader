"""
Pydantic models for API requests and responses
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class OutputFormat(str, Enum):
    """Supported output formats"""
    JSON = "json"
    CSV = "csv"
    TXT = "txt"
    XML = "xml"


class ProcessingStatus(str, Enum):
    """Processing status values"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Request Models
class ProcessPDFRequest(BaseModel):
    """Request model for PDF processing"""
    output_format: OutputFormat = Field(default=OutputFormat.JSON, description="Desired output format")
    approved_only: bool = Field(default=True, description="Export only approved sentences")
    include_metadata: bool = Field(default=True, description="Include processing metadata")
    preserve_context: bool = Field(default=True, description="Preserve sentence context")


class BatchProcessRequest(BaseModel):
    """Request model for batch PDF processing"""
    output_format: OutputFormat = Field(default=OutputFormat.JSON, description="Desired output format")
    approved_only: bool = Field(default=True, description="Export only approved sentences")
    include_metadata: bool = Field(default=True, description="Include processing metadata")
    preserve_context: bool = Field(default=True, description="Preserve sentence context")


# Response Models
class SentenceInfo(BaseModel):
    """Information about a processed sentence"""
    id: int
    text: str
    approved: bool
    quality_grade: str
    word_count: int
    confidence: float
    completeness_score: Optional[float] = None
    clarity_score: Optional[float] = None
    structure_score: Optional[float] = None
    content_score: Optional[float] = None
    translation_readiness_score: Optional[float] = None
    needs_context: Optional[bool] = None
    issues_count: Optional[int] = None


class ProcessingSummary(BaseModel):
    """Summary of processing results"""
    total_sentences: int
    approved_sentences: int
    rejected_sentences: int
    approval_rate: float
    average_quality_score: float
    processing_time: float
    extraction_method: str
    language_detected: Optional[str] = None


class ProcessPDFResponse(BaseModel):
    """Response model for PDF processing"""
    success: bool
    message: str
    session_id: Optional[str] = None
    summary: Optional[ProcessingSummary] = None
    sentences: Optional[List[SentenceInfo]] = None
    formatted_data: Optional[str] = None
    export_path: Optional[str] = None
    error: Optional[str] = None


class BatchProcessResponse(BaseModel):
    """Response model for batch processing"""
    success: bool
    message: str
    batch_id: str
    total_files: int
    processed_files: int
    failed_files: int
    processing_time: float
    results: List[Dict[str, Any]]
    batch_summary: Dict[str, Any]
    error: Optional[str] = None


class ProcessingStatusResponse(BaseModel):
    """Response model for processing status"""
    session_id: str
    status: ProcessingStatus
    progress: float = Field(ge=0.0, le=1.0, description="Processing progress (0-1)")
    message: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Response model for health check"""
    status: str
    timestamp: datetime
    version: str
    components: Dict[str, str]


class ErrorResponse(BaseModel):
    """Standard error response model"""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Configuration Models
class QualityThresholds(BaseModel):
    """Quality threshold configuration"""
    min_completeness: float = Field(ge=0.0, le=1.0, default=0.95)
    min_translation_readiness: float = Field(ge=0.0, le=1.0, default=0.90)
    max_noise_threshold: float = Field(ge=0.0, le=1.0, default=0.05)


class ProcessingConfig(BaseModel):
    """Processing configuration"""
    max_file_size_mb: int = Field(gt=0, default=50)
    batch_size: int = Field(gt=0, default=10)
    processing_timeout: int = Field(gt=0, default=300)
    quality_thresholds: QualityThresholds = Field(default_factory=QualityThresholds)


# Statistics Models
class SystemStats(BaseModel):
    """System statistics"""
    total_documents_processed: int
    total_sentences_extracted: int
    average_processing_time: float
    success_rate: float
    most_common_language: str
    uptime_hours: float


class QualityStats(BaseModel):
    """Quality statistics"""
    average_completeness_score: float
    average_clarity_score: float
    average_structure_score: float
    average_content_score: float
    average_translation_readiness: float
    grade_distribution: Dict[str, int]
