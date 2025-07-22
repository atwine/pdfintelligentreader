"""
Text Preprocessor Agent - Specialized in cleaning and normalizing extracted text
"""

import re
from typing import Dict, Any, List
from crewai import Agent
from loguru import logger
import langdetect

from ..config import settings


class TextPreprocessorAgent:
    """Agent specialized in text cleaning and preprocessing"""
    
    def __init__(self):
        self.agent = self._create_agent()
        logger.info("Text Preprocessor Agent initialized")
    
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent with specialized configuration"""
        return Agent(
            role='Text Preprocessing Specialist',
            goal='Clean and normalize extracted text to prepare it for sentence boundary detection',
            backstory="""You are an expert in text preprocessing and normalization. You understand 
            the common issues that arise from PDF text extraction and know how to clean text while 
            preserving its semantic meaning. Your expertise includes:
            
            - Removing extraction artifacts and formatting noise
            - Normalizing whitespace and line breaks
            - Handling special characters and encoding issues
            - Preserving paragraph structure and context
            - Language detection and character encoding
            - Maintaining text integrity for translation purposes
            
            You ensure that the cleaned text maintains its original meaning while being 
            optimally formatted for further processing.""",
            verbose=True,
            allow_delegation=False,
            tools=[self._preprocess_text, self._detect_language, self._normalize_whitespace]
        )
    
    def _preprocess_text(self, raw_text: str, preserve_structure: bool = True) -> Dict[str, Any]:
        """
        Comprehensive text preprocessing
        
        Args:
            raw_text: Raw extracted text from PDF
            preserve_structure: Whether to preserve paragraph structure
            
        Returns:
            Dictionary containing cleaned text and preprocessing metadata
        """
        try:
            logger.info("Text Preprocessor Agent processing text")
            
            if not raw_text or not raw_text.strip():
                return {
                    "success": False,
                    "error": "Empty or invalid input text",
                    "cleaned_text": "",
                    "language": "unknown",
                    "preprocessing_stats": {}
                }
            
            original_length = len(raw_text)
            
            # Step 1: Basic cleaning
            cleaned_text = self._basic_cleaning(raw_text)
            
            # Step 2: Normalize whitespace
            cleaned_text = self._normalize_whitespace_internal(cleaned_text, preserve_structure)
            
            # Step 3: Remove extraction artifacts
            cleaned_text = self._remove_artifacts(cleaned_text)
            
            # Step 4: Fix common OCR errors
            cleaned_text = self._fix_ocr_errors(cleaned_text)
            
            # Step 5: Language detection
            language = self._detect_language_internal(cleaned_text)
            
            # Calculate preprocessing statistics
            final_length = len(cleaned_text)
            stats = {
                "original_length": original_length,
                "final_length": final_length,
                "reduction_percentage": ((original_length - final_length) / original_length * 100) if original_length > 0 else 0,
                "estimated_sentences": len(re.findall(r'[.!?]+', cleaned_text)),
                "estimated_paragraphs": len([p for p in cleaned_text.split('\n\n') if p.strip()])
            }
            
            logger.success(f"Text preprocessing completed. Reduced by {stats['reduction_percentage']:.1f}%")
            
            return {
                "success": True,
                "cleaned_text": cleaned_text,
                "language": language,
                "preprocessing_stats": stats
            }
            
        except Exception as e:
            error_msg = f"Text preprocessing error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "cleaned_text": raw_text,  # Return original on error
                "language": "unknown",
                "preprocessing_stats": {}
            }
    
    def _basic_cleaning(self, text: str) -> str:
        """Basic text cleaning operations"""
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Fix common encoding issues
        text = text.replace('\ufeff', '')  # Remove BOM
        text = text.replace('\u00a0', ' ')  # Replace non-breaking space
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)  # Normalize ellipsis
        text = re.sub(r'[-]{3,}', '---', text)  # Normalize dashes
        
        return text
    
    def _normalize_whitespace_internal(self, text: str, preserve_structure: bool) -> str:
        """Normalize whitespace while preserving structure"""
        if preserve_structure:
            # Preserve paragraph breaks (double newlines)
            paragraphs = text.split('\n\n')
            normalized_paragraphs = []
            
            for paragraph in paragraphs:
                # Normalize within paragraph
                paragraph = re.sub(r'\s+', ' ', paragraph.strip())
                if paragraph:
                    normalized_paragraphs.append(paragraph)
            
            return '\n\n'.join(normalized_paragraphs)
        else:
            # Simple whitespace normalization
            return re.sub(r'\s+', ' ', text.strip())
    
    def _remove_artifacts(self, text: str) -> str:
        """Remove common PDF extraction artifacts"""
        # Remove page numbers (standalone numbers)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        
        # Remove headers/footers (repeated short lines)
        lines = text.split('\n')
        cleaned_lines = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                cleaned_lines.append('')
                continue
                
            # Skip very short lines that appear multiple times (likely headers/footers)
            if len(line) < 30:
                line_count = sum(1 for l in lines if l.strip() == line)
                if line_count > 2:  # Appears more than twice
                    continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _fix_ocr_errors(self, text: str) -> str:
        """Fix common OCR errors"""
        # Common OCR character substitutions
        ocr_fixes = {
            r'\bl\b': 'I',  # Standalone 'l' often should be 'I'
            r'\b0\b': 'O',  # Standalone '0' in text often should be 'O'
            r'rn': 'm',     # 'rn' often misread as 'm'
            r'vv': 'w',     # 'vv' often misread as 'w'
            r'\bfi\b': 'fi', # ligature fixes
        }
        
        for pattern, replacement in ocr_fixes.items():
            text = re.sub(pattern, replacement, text)
        
        return text
    
    def _detect_language_internal(self, text: str) -> str:
        """Detect text language"""
        try:
            if len(text.strip()) < 50:
                return "unknown"
            
            # Use first 1000 characters for detection
            sample = text[:1000]
            detected = langdetect.detect(sample)
            return detected
        except:
            return "en"  # Default to English
    
    def _detect_language(self, text: str) -> Dict[str, Any]:
        """Tool function for language detection"""
        language = self._detect_language_internal(text)
        return {"language": language}
    
    def _normalize_whitespace(self, text: str, preserve_structure: bool = True) -> Dict[str, Any]:
        """Tool function for whitespace normalization"""
        normalized = self._normalize_whitespace_internal(text, preserve_structure)
        return {"normalized_text": normalized}
    
    def get_agent(self) -> Agent:
        """Get the CrewAI agent instance"""
        return self.agent
    
    def process_text(self, raw_text: str, preserve_structure: bool = True) -> Dict[str, Any]:
        """
        Process raw text through preprocessing pipeline
        
        Args:
            raw_text: Raw extracted text
            preserve_structure: Whether to preserve paragraph structure
            
        Returns:
            Dictionary containing processed text and metadata
        """
        return self._preprocess_text(raw_text, preserve_structure)
