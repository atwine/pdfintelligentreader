"""
Multi-method PDF text extraction with fallback strategy
"""

import os
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from loguru import logger

from ..config import settings


@dataclass
class ExtractionResult:
    """Result of PDF text extraction"""
    text: str
    method: str
    confidence: float
    processing_time: float
    page_count: int
    metadata: Dict
    success: bool
    error_message: Optional[str] = None


class PDFExtractor:
    """Multi-method PDF text extractor with intelligent fallback"""
    
    def __init__(self):
        self.extraction_methods = [
            ("pymupdf", self._extract_with_pymupdf),
            ("pdfplumber", self._extract_with_pdfplumber),
            ("ocr", self._extract_with_ocr)
        ]
        logger.info("PDF Extractor initialized with multi-method fallback")
    
    def extract_text(self, pdf_path: str) -> ExtractionResult:
        """
        Extract text using multi-method approach with fallback
        
        Priority order:
        1. PyMuPDF (fastest, good for native text)
        2. pdfplumber (better for tables and layout)
        3. OCR (for scanned documents)
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            return ExtractionResult(
                text="", method="none", confidence=0.0, processing_time=0.0,
                page_count=0, metadata={}, success=False,
                error_message=f"File not found: {pdf_path}"
            )
        
        logger.info(f"Starting text extraction for: {pdf_path.name}")
        
        # Try each extraction method in order
        for method_name, method_func in self.extraction_methods:
            try:
                result = method_func(str(pdf_path))
                if result.success and self._is_extraction_quality_acceptable(result):
                    logger.success(f"Successfully extracted text using {method_name}")
                    return result
                else:
                    logger.warning(f"Method {method_name} failed or produced low-quality results")
            except Exception as e:
                logger.error(f"Method {method_name} failed with error: {str(e)}")
                continue
        
        # If all methods fail
        return ExtractionResult(
            text="", method="failed", confidence=0.0, processing_time=0.0,
            page_count=0, metadata={}, success=False,
            error_message="All extraction methods failed"
        )
    
    def _extract_with_pymupdf(self, pdf_path: str) -> ExtractionResult:
        """Extract text using PyMuPDF (fastest method)"""
        start_time = time.time()
        
        try:
            doc = fitz.open(pdf_path)
            text_parts = []
            metadata = {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "creator": doc.metadata.get("creator", "")
            }
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)
            
            doc.close()
            
            full_text = "\n".join(text_parts)
            processing_time = time.time() - start_time
            
            # Calculate confidence based on text quality
            confidence = self._calculate_text_confidence(full_text)
            
            return ExtractionResult(
                text=full_text,
                method="pymupdf",
                confidence=confidence,
                processing_time=processing_time,
                page_count=len(doc),
                metadata=metadata,
                success=True
            )
            
        except Exception as e:
            return ExtractionResult(
                text="", method="pymupdf", confidence=0.0,
                processing_time=time.time() - start_time,
                page_count=0, metadata={}, success=False,
                error_message=str(e)
            )
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> ExtractionResult:
        """Extract text using pdfplumber (better for complex layouts)"""
        start_time = time.time()
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_parts = []
                metadata = pdf.metadata or {}
                
                for page in pdf.pages:
                    text = page.extract_text()
                    if text and text.strip():
                        text_parts.append(text)
                
                full_text = "\n".join(text_parts)
                processing_time = time.time() - start_time
                
                # Calculate confidence based on text quality
                confidence = self._calculate_text_confidence(full_text)
                
                return ExtractionResult(
                    text=full_text,
                    method="pdfplumber",
                    confidence=confidence,
                    processing_time=processing_time,
                    page_count=len(pdf.pages),
                    metadata=metadata,
                    success=True
                )
                
        except Exception as e:
            return ExtractionResult(
                text="", method="pdfplumber", confidence=0.0,
                processing_time=time.time() - start_time,
                page_count=0, metadata={}, success=False,
                error_message=str(e)
            )
    
    def _extract_with_ocr(self, pdf_path: str) -> ExtractionResult:
        """Extract text using OCR (for scanned documents)"""
        start_time = time.time()
        
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            text_parts = []
            
            for i, image in enumerate(images):
                # Perform OCR on each page
                text = pytesseract.image_to_string(image, lang='eng')
                if text.strip():
                    text_parts.append(text)
                
                logger.info(f"OCR processed page {i+1}/{len(images)}")
            
            full_text = "\n".join(text_parts)
            processing_time = time.time() - start_time
            
            # OCR confidence is generally lower
            confidence = self._calculate_text_confidence(full_text) * 0.8
            
            return ExtractionResult(
                text=full_text,
                method="ocr",
                confidence=confidence,
                processing_time=processing_time,
                page_count=len(images),
                metadata={"ocr_language": "eng"},
                success=True
            )
            
        except Exception as e:
            return ExtractionResult(
                text="", method="ocr", confidence=0.0,
                processing_time=time.time() - start_time,
                page_count=0, metadata={}, success=False,
                error_message=str(e)
            )
    
    def _calculate_text_confidence(self, text: str) -> float:
        """Calculate confidence score based on text quality indicators"""
        if not text or not text.strip():
            return 0.0
        
        # Basic quality indicators
        total_chars = len(text)
        alpha_chars = sum(1 for c in text if c.isalpha())
        digit_chars = sum(1 for c in text if c.isdigit())
        space_chars = sum(1 for c in text if c.isspace())
        punct_chars = sum(1 for c in text if c in '.,!?;:')
        
        # Calculate ratios
        alpha_ratio = alpha_chars / total_chars if total_chars > 0 else 0
        digit_ratio = digit_chars / total_chars if total_chars > 0 else 0
        space_ratio = space_chars / total_chars if total_chars > 0 else 0
        punct_ratio = punct_chars / total_chars if total_chars > 0 else 0
        
        # Quality score based on expected text characteristics
        confidence = 0.0
        
        # Good alpha ratio (60-85%)
        if 0.6 <= alpha_ratio <= 0.85:
            confidence += 0.4
        
        # Reasonable space ratio (10-20%)
        if 0.1 <= space_ratio <= 0.2:
            confidence += 0.2
        
        # Some punctuation (1-5%)
        if 0.01 <= punct_ratio <= 0.05:
            confidence += 0.2
        
        # Not too many digits (less than 20%)
        if digit_ratio < 0.2:
            confidence += 0.1
        
        # Minimum length check
        if total_chars > 100:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _is_extraction_quality_acceptable(self, result: ExtractionResult) -> bool:
        """Check if extraction quality meets minimum standards"""
        if not result.success or not result.text:
            return False
        
        # Minimum confidence threshold
        if result.confidence < 0.3:
            return False
        
        # Minimum text length
        if len(result.text.strip()) < 50:
            return False
        
        return True
