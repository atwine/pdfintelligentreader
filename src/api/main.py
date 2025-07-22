"""
FastAPI main application for PDF Intelligent Reader
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from .models import *
from .endpoints.processing import router as processing_router
from .endpoints.batch import router as batch_router
from .endpoints.status import router as status_router
from ..config import settings
from ..intelligence.pdf_processing_crew import PDFProcessingCrew
from ..models.document import create_database

# Initialize database
create_database(settings.database_url)

# Initialize FastAPI app
app = FastAPI(
    title="PDF Intelligent Reader API",
    description="Intelligent PDF data extraction system for translation activities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize PDF processing crew
pdf_crew = PDFProcessingCrew()

# In-memory storage for processing status (use Redis in production)
processing_status: Dict[str, Dict[str, Any]] = {}

# Include routers
app.include_router(processing_router, prefix="/api/v1", tags=["processing"])
app.include_router(batch_router, prefix="/api/v1", tags=["batch"])
app.include_router(status_router, prefix="/api/v1", tags=["status"])

# Create necessary directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("output", exist_ok=True)
os.makedirs("temp", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "PDF Intelligent Reader API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check system components
        components = {
            "database": "healthy",
            "pdf_crew": "healthy" if pdf_crew.crew else "unhealthy",
            "storage": "healthy" if os.path.exists("uploads") else "unhealthy",
            "openai": "healthy"  # Could add actual API check
        }
        
        overall_status = "healthy" if all(status == "healthy" for status in components.values()) else "unhealthy"
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version="1.0.0",
            components=components
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            components={"error": str(e)}
        )


@app.post("/api/v1/upload", response_model=Dict[str, str])
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF file for processing"""
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Check file size
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        unique_filename = f"{file_id}{file_extension}"
        file_path = Path("uploads") / unique_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"File uploaded: {file.filename} -> {unique_filename}")
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "file_path": str(file_path),
            "file_size": file_size,
            "message": "File uploaded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/v1/process", response_model=ProcessPDFResponse)
async def process_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    request: ProcessPDFRequest = Depends()
):
    """Process a PDF file"""
    try:
        # Upload file first
        upload_result = await upload_pdf(file)
        file_path = upload_result["file_path"]
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Update processing status
        processing_status[session_id] = {
            "status": ProcessingStatus.PROCESSING,
            "progress": 0.0,
            "message": "Processing started",
            "started_at": datetime.utcnow(),
            "file_path": file_path
        }
        
        # Start background processing
        background_tasks.add_task(
            process_pdf_background,
            session_id,
            file_path,
            request
        )
        
        return ProcessPDFResponse(
            success=True,
            message="Processing started",
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"PDF processing request failed: {str(e)}")
        return ProcessPDFResponse(
            success=False,
            message="Processing failed to start",
            error=str(e)
        )


async def process_pdf_background(session_id: str, file_path: str, request: ProcessPDFRequest):
    """Background task for PDF processing"""
    try:
        logger.info(f"Starting background processing for session {session_id}")
        
        # Update status
        processing_status[session_id].update({
            "progress": 0.1,
            "message": "Initializing processing"
        })
        
        # Determine output path
        output_path = None
        if request.output_format:
            output_filename = f"{session_id}_output.{request.output_format.value}"
            output_path = str(Path("output") / output_filename)
        
        # Process PDF using crew
        result = pdf_crew.process_pdf(
            pdf_path=file_path,
            output_format=request.output_format.value,
            output_path=output_path
        )
        
        # Update final status
        if result.get("success", False):
            processing_status[session_id].update({
                "status": ProcessingStatus.COMPLETED,
                "progress": 1.0,
                "message": "Processing completed successfully",
                "completed_at": datetime.utcnow(),
                "result": result
            })
        else:
            processing_status[session_id].update({
                "status": ProcessingStatus.FAILED,
                "progress": 1.0,
                "message": "Processing failed",
                "completed_at": datetime.utcnow(),
                "error": result.get("error", "Unknown error")
            })
        
        logger.info(f"Background processing completed for session {session_id}")
        
    except Exception as e:
        logger.error(f"Background processing failed for session {session_id}: {str(e)}")
        processing_status[session_id].update({
            "status": ProcessingStatus.FAILED,
            "progress": 1.0,
            "message": "Processing failed",
            "completed_at": datetime.utcnow(),
            "error": str(e)
        })


@app.get("/api/v1/status/{session_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(session_id: str):
    """Get processing status for a session"""
    if session_id not in processing_status:
        raise HTTPException(status_code=404, detail="Session not found")
    
    status_data = processing_status[session_id]
    
    return ProcessingStatusResponse(
        session_id=session_id,
        status=status_data["status"],
        progress=status_data["progress"],
        message=status_data["message"],
        started_at=status_data.get("started_at"),
        completed_at=status_data.get("completed_at"),
        error=status_data.get("error")
    )


@app.get("/api/v1/result/{session_id}")
async def get_processing_result(session_id: str):
    """Get processing result for a completed session"""
    if session_id not in processing_status:
        raise HTTPException(status_code=404, detail="Session not found")
    
    status_data = processing_status[session_id]
    
    if status_data["status"] != ProcessingStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Processing not completed")
    
    result = status_data.get("result", {})
    
    # Check if there's an output file
    if "export_result" in result and result["export_result"].get("success", False):
        output_path = result["export_result"]["output_path"]
        if os.path.exists(output_path):
            return FileResponse(
                path=output_path,
                filename=f"processed_{session_id}.{Path(output_path).suffix[1:]}",
                media_type="application/octet-stream"
            )
    
    # Return JSON result
    return JSONResponse(content=result)


@app.get("/api/v1/stats", response_model=SystemStats)
async def get_system_stats():
    """Get system statistics"""
    # This would typically query the database
    # For now, return mock data
    return SystemStats(
        total_documents_processed=0,
        total_sentences_extracted=0,
        average_processing_time=0.0,
        success_rate=0.0,
        most_common_language="en",
        uptime_hours=0.0
    )


@app.get("/api/v1/config", response_model=ProcessingConfig)
async def get_processing_config():
    """Get current processing configuration"""
    return ProcessingConfig(
        max_file_size_mb=settings.max_file_size_mb,
        batch_size=settings.batch_size,
        processing_timeout=settings.processing_timeout,
        quality_thresholds=QualityThresholds(
            min_completeness=settings.min_sentence_completeness,
            min_translation_readiness=settings.min_translation_readiness,
            max_noise_threshold=settings.max_noise_threshold
        )
    )


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            error_code=str(exc.status_code)
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            error_code="500",
            details={"message": str(exc)} if settings.debug else None
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
