"""
Basic functionality tests for PDF Intelligent Reader
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.config import settings
from src.tools.pdf_extractor import PDFExtractor
from src.agents.text_preprocessor_agent import TextPreprocessorAgent
from src.agents.sentence_boundary_agent import SentenceBoundaryAgent


class TestPDFExtractor:
    """Test PDF extraction functionality"""
    
    def test_extractor_initialization(self):
        """Test PDF extractor initialization"""
        extractor = PDFExtractor()
        assert extractor is not None
        assert len(extractor.extraction_methods) == 3
        assert extractor.extraction_methods[0][0] == "pymupdf"
        assert extractor.extraction_methods[1][0] == "pdfplumber"
        assert extractor.extraction_methods[2][0] == "ocr"
    
    def test_confidence_calculation(self):
        """Test text confidence calculation"""
        extractor = PDFExtractor()
        
        # Test good quality text
        good_text = "This is a well-formed sentence with proper punctuation. It contains meaningful content."
        confidence = extractor._calculate_text_confidence(good_text)
        assert confidence > 0.5
        
        # Test poor quality text
        poor_text = "abc123!@#$%^&*()"
        confidence = extractor._calculate_text_confidence(poor_text)
        assert confidence < 0.5
        
        # Test empty text
        empty_confidence = extractor._calculate_text_confidence("")
        assert empty_confidence == 0.0


class TestTextPreprocessor:
    """Test text preprocessing functionality"""
    
    def test_preprocessor_initialization(self):
        """Test text preprocessor initialization"""
        preprocessor = TextPreprocessorAgent()
        assert preprocessor is not None
        assert preprocessor.agent is not None
    
    def test_basic_cleaning(self):
        """Test basic text cleaning"""
        preprocessor = TextPreprocessorAgent()
        
        # Test text with artifacts
        dirty_text = "This is a test\x00\x01 with control characters\ufeff and BOM."
        cleaned = preprocessor._basic_cleaning(dirty_text)
        
        assert "\x00" not in cleaned
        assert "\x01" not in cleaned
        assert "\ufeff" not in cleaned
    
    def test_whitespace_normalization(self):
        """Test whitespace normalization"""
        preprocessor = TextPreprocessorAgent()
        
        # Test with excessive whitespace
        messy_text = "This   has    too     much\n\n\n\nwhitespace."
        normalized = preprocessor._normalize_whitespace_internal(messy_text, preserve_structure=False)
        
        assert "   " not in normalized
        assert normalized.strip() == "This has too much whitespace."
    
    def test_language_detection(self):
        """Test language detection"""
        preprocessor = TextPreprocessorAgent()
        
        # Test English text
        english_text = "This is a sentence in English language with sufficient content for detection."
        language = preprocessor._detect_language_internal(english_text)
        
        # Should detect English or return default
        assert language in ["en", "unknown"]


class TestSentenceBoundary:
    """Test sentence boundary detection"""
    
    def test_boundary_agent_initialization(self):
        """Test sentence boundary agent initialization"""
        agent = SentenceBoundaryAgent()
        assert agent is not None
        assert agent.agent is not None
    
    def test_nltk_sentence_detection(self):
        """Test NLTK sentence detection"""
        agent = SentenceBoundaryAgent()
        
        text = "This is the first sentence. This is the second sentence! Is this the third sentence?"
        sentences = agent._nltk_sentence_detection(text)
        
        assert len(sentences) >= 3
        assert all("text" in sentence for sentence in sentences)
        assert all("confidence" in sentence for sentence in sentences)
    
    def test_sentence_validation(self):
        """Test sentence validation"""
        agent = SentenceBoundaryAgent()
        
        # Create test sentences
        test_sentences = [
            {"text": "This is a complete sentence.", "confidence": 0.9},
            {"text": "Too short.", "confidence": 0.8},
            {"text": "123456789", "confidence": 0.7},  # Mostly numbers
            {"text": "This is a properly formed sentence with good content.", "confidence": 0.95}
        ]
        
        validated = agent._validate_and_clean_sentences(test_sentences)
        
        # Should filter out short and number-heavy sentences
        assert len(validated) <= len(test_sentences)
        assert all(len(s["text"]) >= 10 for s in validated)


class TestConfiguration:
    """Test configuration and settings"""
    
    def test_settings_loading(self):
        """Test that settings load properly"""
        assert settings is not None
        assert hasattr(settings, 'max_file_size_mb')
        assert hasattr(settings, 'min_sentence_completeness')
        assert hasattr(settings, 'min_translation_readiness')
    
    def test_quality_thresholds(self):
        """Test quality threshold values"""
        assert 0.0 <= settings.min_sentence_completeness <= 1.0
        assert 0.0 <= settings.min_translation_readiness <= 1.0
        assert 0.0 <= settings.max_noise_threshold <= 1.0


class TestIntegration:
    """Integration tests"""
    
    def test_agent_chain_compatibility(self):
        """Test that agents can work together"""
        # Initialize agents
        preprocessor = TextPreprocessorAgent()
        boundary_agent = SentenceBoundaryAgent()
        
        # Test data flow
        test_text = "This is a test document. It contains multiple sentences. Each sentence should be processed correctly."
        
        # Step 1: Preprocess
        preprocess_result = preprocessor.process_text(test_text)
        assert preprocess_result["success"] == True
        
        # Step 2: Sentence boundary detection
        boundary_result = boundary_agent.process_text(preprocess_result["cleaned_text"])
        assert boundary_result["success"] == True
        assert len(boundary_result["sentences"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
