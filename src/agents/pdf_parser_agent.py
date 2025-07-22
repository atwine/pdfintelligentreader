"""
PDF Parser Agent - Specialized in extracting text from PDF documents
"""

from typing import Dict, Any, List
from crewai import Agent
from loguru import logger

from ..tools.pdf_extractor import PDFExtractor
from ..config import settings


class PDFParserAgent:
    """Agent specialized in PDF text extraction with multi-method fallback"""
    
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.agent = self._create_agent()
        logger.info("PDF Parser Agent initialized")
    
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent with specialized configuration"""
        return Agent(
            role='PDF Parser Specialist',
            goal='Extract clean, accurate text from PDF documents using optimal extraction methods',
            backstory="""You are an expert in PDF processing with deep knowledge of multiple 
            extraction methods. You understand the nuances of different PDF formats - from native 
            text PDFs to scanned documents requiring OCR. Your expertise includes:
            
            - PyMuPDF for fast native text extraction
            - pdfplumber for complex layouts and tables
            - OCR processing for scanned documents
            - Quality assessment of extracted text
            - Fallback strategies for problematic documents
            
            You always choose the most appropriate extraction method and provide detailed 
            metadata about the extraction process.""",
            verbose=True,
            allow_delegation=False,
            tools=[self._extract_pdf_text]
        )
    
    def _extract_pdf_text(self, pdf_path: str) -> Dict[str, Any]:
        """
        Tool function for extracting text from PDF
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            logger.info(f"PDF Parser Agent processing: {pdf_path}")
            
            # Use the multi-method extractor
            result = self.pdf_extractor.extract_text(pdf_path)
            
            # Format response for CrewAI
            response = {
                "success": result.success,
                "text": result.text,
                "extraction_method": result.method,
                "confidence": result.confidence,
                "processing_time": result.processing_time,
                "page_count": result.page_count,
                "metadata": result.metadata,
                "file_path": pdf_path
            }
            
            if not result.success:
                response["error"] = result.error_message
                logger.error(f"PDF extraction failed: {result.error_message}")
            else:
                logger.success(f"PDF extracted successfully using {result.method} "
                             f"(confidence: {result.confidence:.2f})")
            
            return response
            
        except Exception as e:
            error_msg = f"PDF Parser Agent error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "text": "",
                "extraction_method": "failed",
                "confidence": 0.0,
                "processing_time": 0.0,
                "page_count": 0,
                "metadata": {},
                "file_path": pdf_path
            }
    
    def get_agent(self) -> Agent:
        """Get the CrewAI agent instance"""
        return self.agent
    
    def process_document(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process a PDF document and return extraction results
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing extraction results and metadata
        """
        return self._extract_pdf_text(pdf_path)
