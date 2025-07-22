"""
PDF Intelligent Reader - Main Application Entry Point
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import settings
from src.intelligence.pdf_processing_crew import PDFProcessingCrew
from src.models.document import create_database
from loguru import logger


def setup_environment():
    """Setup application environment"""
    # Create necessary directories
    directories = ["logs", "uploads", "output", "temp"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # Initialize database
    create_database(settings.database_url)
    logger.info("Environment setup completed")


def process_single_pdf(pdf_path: str, output_format: str = "json", output_path: Optional[str] = None):
    """Process a single PDF file"""
    try:
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Initialize crew
        crew = PDFProcessingCrew()
        
        # Process PDF
        result = crew.process_pdf(
            pdf_path=pdf_path,
            output_format=output_format,
            output_path=output_path
        )
        
        if result.get("success", False):
            logger.success("PDF processing completed successfully")
            
            # Print summary
            summary = result.get("summary", {})
            if summary:
                print("\n" + "="*50)
                print("PROCESSING SUMMARY")
                print("="*50)
                print(f"Total Sentences: {summary.get('total_sentences', 0)}")
                print(f"Approved Sentences: {summary.get('approved_sentences', 0)}")
                print(f"Approval Rate: {summary.get('approval_rate', 0):.1%}")
                print(f"Average Quality: {summary.get('average_quality_score', 0):.2f}")
                print(f"Processing Time: {summary.get('processing_time', 0):.2f}s")
                print(f"Language: {summary.get('language_detected', 'Unknown')}")
                
                if output_path:
                    print(f"Output File: {output_path}")
                print("="*50)
        else:
            logger.error(f"PDF processing failed: {result.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        return False


def process_batch(pdf_directory: str, output_format: str = "json", output_directory: Optional[str] = None):
    """Process multiple PDF files in a directory"""
    try:
        pdf_dir = Path(pdf_directory)
        if not pdf_dir.exists():
            logger.error(f"Directory not found: {pdf_directory}")
            return False
        
        # Find PDF files
        pdf_files = list(pdf_dir.glob("*.pdf"))
        if not pdf_files:
            logger.error(f"No PDF files found in {pdf_directory}")
            return False
        
        logger.info(f"Found {len(pdf_files)} PDF files for batch processing")
        
        # Initialize crew
        crew = PDFProcessingCrew()
        
        # Process batch
        result = crew.process_batch(
            pdf_paths=[str(f) for f in pdf_files],
            output_format=output_format,
            output_dir=output_directory
        )
        
        if result.get("success", False):
            logger.success("Batch processing completed successfully")
            
            # Print batch summary
            print("\n" + "="*50)
            print("BATCH PROCESSING SUMMARY")
            print("="*50)
            print(f"Total Files: {result['total_files']}")
            print(f"Processed Successfully: {result['processed_files']}")
            print(f"Failed: {result['failed_files']}")
            print(f"Success Rate: {result['processed_files']/result['total_files']:.1%}")
            print(f"Total Processing Time: {result['processing_time']:.2f}s")
            
            batch_summary = result.get('batch_summary', {})
            if batch_summary:
                print(f"Average Processing Time: {batch_summary.get('avg_processing_time', 0):.2f}s")
                print(f"Total Sentences: {batch_summary.get('total_sentences', 0)}")
                print(f"Average Quality Score: {batch_summary.get('avg_quality_score', 0):.2f}")
            
            if output_directory:
                print(f"Output Directory: {output_directory}")
            print("="*50)
        else:
            logger.error(f"Batch processing failed: {result.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}")
        return False


def start_api_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Start the FastAPI server"""
    try:
        import uvicorn
        from src.api.main import app
        
        logger.info(f"Starting API server on {host}:{port}")
        
        uvicorn.run(
            "src.api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"Failed to start API server: {str(e)}")
        return False


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description="PDF Intelligent Reader")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Process single PDF command
    process_parser = subparsers.add_parser("process", help="Process a single PDF file")
    process_parser.add_argument("pdf_path", help="Path to PDF file")
    process_parser.add_argument("--format", choices=["json", "csv", "txt", "xml"], 
                               default="json", help="Output format")
    process_parser.add_argument("--output", help="Output file path")
    
    # Batch processing command
    batch_parser = subparsers.add_parser("batch", help="Process multiple PDF files")
    batch_parser.add_argument("pdf_directory", help="Directory containing PDF files")
    batch_parser.add_argument("--format", choices=["json", "csv", "txt", "xml"], 
                             default="json", help="Output format")
    batch_parser.add_argument("--output-dir", help="Output directory")
    
    # API server command
    api_parser = subparsers.add_parser("api", help="Start API server")
    api_parser.add_argument("--host", default="0.0.0.0", help="Host address")
    api_parser.add_argument("--port", type=int, default=8000, help="Port number")
    api_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Setup environment")
    
    args = parser.parse_args()
    
    # Setup environment
    setup_environment()
    
    # Execute command
    if args.command == "process":
        success = process_single_pdf(args.pdf_path, args.format, args.output)
        sys.exit(0 if success else 1)
        
    elif args.command == "batch":
        success = process_batch(args.pdf_directory, args.format, args.output_dir)
        sys.exit(0 if success else 1)
        
    elif args.command == "api":
        start_api_server(args.host, args.port, args.reload)
        
    elif args.command == "setup":
        logger.success("Environment setup completed")
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
