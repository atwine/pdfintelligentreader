"""
Integration tests for PDF Intelligent Reader
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.intelligence.pdf_processing_crew import PDFProcessingCrew
from src.agents.text_preprocessor_agent import TextPreprocessorAgent
from src.agents.sentence_boundary_agent import SentenceBoundaryAgent
from src.agents.quality_assurance_agent import QualityAssuranceAgent


class TestEndToEndProcessing:
    """Test complete processing pipeline"""
    
    @pytest.fixture
    def sample_text(self):
        """Sample text for testing"""
        return """
        This is a sample document for testing the PDF processing pipeline. 
        It contains multiple sentences with varying complexity. Some sentences 
        are simple and straightforward. Others may contain more complex 
        grammatical structures and technical terminology.
        
        The quality assurance system should evaluate each sentence based on 
        completeness, clarity, structure, and content quality. Translation 
        readiness scores should reflect the suitability of each sentence 
        for professional translation work.
        """
    
    def test_text_preprocessing_pipeline(self, sample_text):
        """Test text preprocessing pipeline"""
        preprocessor = TextPreprocessorAgent()
        
        result = preprocessor.process_text(sample_text, preserve_structure=True)
        
        assert result["success"] == True
        assert "cleaned_text" in result
        assert "language" in result
        assert "preprocessing_stats" in result
        
        # Check that text was cleaned
        cleaned_text = result["cleaned_text"]
        assert len(cleaned_text) > 0
        assert cleaned_text != sample_text  # Should be different after cleaning
        
        # Check statistics
        stats = result["preprocessing_stats"]
        assert "original_length" in stats
        assert "final_length" in stats
        assert "estimated_sentences" in stats
    
    def test_sentence_boundary_detection(self, sample_text):
        """Test sentence boundary detection"""
        # First preprocess
        preprocessor = TextPreprocessorAgent()
        preprocess_result = preprocessor.process_text(sample_text)
        
        # Then detect boundaries
        boundary_agent = SentenceBoundaryAgent()
        result = boundary_agent.process_text(preprocess_result["cleaned_text"])
        
        assert result["success"] == True
        assert "sentences" in result
        assert len(result["sentences"]) > 0
        
        # Check sentence structure
        sentences = result["sentences"]
        for sentence in sentences:
            assert "text" in sentence
            assert "confidence" in sentence
            assert "method" in sentence
            assert len(sentence["text"].strip()) > 0
    
    def test_quality_assessment_pipeline(self, sample_text):
        """Test complete quality assessment pipeline"""
        # Process through preprocessing and boundary detection
        preprocessor = TextPreprocessorAgent()
        preprocess_result = preprocessor.process_text(sample_text)
        
        boundary_agent = SentenceBoundaryAgent()
        boundary_result = boundary_agent.process_text(preprocess_result["cleaned_text"])
        
        # Run quality assessment
        qa_agent = QualityAssuranceAgent()
        result = qa_agent.process_sentences(boundary_result["sentences"])
        
        assert result["success"] == True
        assert "quality_results" in result
        assert "batch_metrics" in result
        
        # Check quality results structure
        quality_results = result["quality_results"]
        assert len(quality_results) > 0
        
        for sentence_result in quality_results:
            assert "quality_scores" in sentence_result
            assert "translation_readiness" in sentence_result
            assert "approved" in sentence_result
            assert "quality_grade" in sentence_result
            
            # Check quality scores
            quality_scores = sentence_result["quality_scores"]
            assert "completeness" in quality_scores
            assert "clarity" in quality_scores
            assert "structure" in quality_scores
            assert "content" in quality_scores
            
            # Check translation readiness
            translation_readiness = sentence_result["translation_readiness"]
            assert "score" in translation_readiness
            assert "level" in translation_readiness
            assert "ready_for_translation" in translation_readiness


class TestCrewIntegration:
    """Test CrewAI integration"""
    
    def test_crew_initialization(self):
        """Test PDF processing crew initialization"""
        crew = PDFProcessingCrew()
        
        assert crew is not None
        assert crew.crew is not None
        assert crew.tasks_manager is not None
        
        # Check crew info
        info = crew.get_crew_info()
        assert "agents_count" in info
        assert info["agents_count"] > 0
        assert info["process_type"] == "sequential"
    
    @patch('src.intelligence.pdf_processing_crew.Path.exists')
    def test_pdf_processing_validation(self, mock_exists):
        """Test PDF processing with mocked file"""
        mock_exists.return_value = True
        
        crew = PDFProcessingCrew()
        
        # Mock the crew execution
        with patch.object(crew.crew, 'kickoff') as mock_kickoff:
            mock_kickoff.return_value = {
                "success": True,
                "formatted_data": '{"test": "data"}',
                "summary": {"total_sentences": 5}
            }
            
            result = crew.process_pdf("test.pdf", "json")
            
            assert result["success"] == True
            assert "pdf_path" in result
            assert "processing_time" in result


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_empty_text_handling(self):
        """Test handling of empty text"""
        preprocessor = TextPreprocessorAgent()
        result = preprocessor.process_text("")
        
        assert result["success"] == False
        assert "error" in result
    
    def test_invalid_text_handling(self):
        """Test handling of invalid text"""
        boundary_agent = SentenceBoundaryAgent()
        result = boundary_agent.process_text(None)
        
        # Should handle gracefully
        assert "success" in result
    
    def test_quality_assessment_empty_input(self):
        """Test quality assessment with empty input"""
        qa_agent = QualityAssuranceAgent()
        result = qa_agent.process_sentences([])
        
        assert result["success"] == False
        assert "error" in result


class TestConfigurationValidation:
    """Test configuration validation"""
    
    def test_quality_thresholds(self):
        """Test quality threshold validation"""
        from src.config import settings
        
        # Check that thresholds are within valid ranges
        assert 0.0 <= settings.min_sentence_completeness <= 1.0
        assert 0.0 <= settings.min_translation_readiness <= 1.0
        assert 0.0 <= settings.max_noise_threshold <= 1.0
        
        # Check reasonable values
        assert settings.min_sentence_completeness >= 0.8  # Should be high
        assert settings.min_translation_readiness >= 0.8  # Should be high
        assert settings.max_noise_threshold <= 0.1       # Should be low


class TestOutputFormatting:
    """Test output formatting"""
    
    def test_json_formatting(self):
        """Test JSON output formatting"""
        from src.agents.output_formatter_agent import OutputFormatterAgent
        
        formatter = OutputFormatterAgent()
        
        # Mock quality results
        mock_results = [
            {
                "text": "This is a test sentence.",
                "approved": True,
                "quality_grade": "A",
                "quality_scores": {"completeness": 0.95, "clarity": 0.90},
                "translation_readiness": {"score": 0.92, "level": "excellent"},
                "sentence_index": 0,
                "word_count": 5
            }
        ]
        
        result = formatter._format_output(mock_results, "json", True, False)
        
        assert result["success"] == True
        assert "formatted_data" in result
        
        # Parse JSON to validate structure
        formatted_data = json.loads(result["formatted_data"])
        assert "metadata" in formatted_data
        assert "sentences" in formatted_data
        assert len(formatted_data["sentences"]) == 1
    
    def test_csv_formatting(self):
        """Test CSV output formatting"""
        from src.agents.output_formatter_agent import OutputFormatterAgent
        
        formatter = OutputFormatterAgent()
        
        mock_results = [
            {
                "text": "Test sentence.",
                "approved": True,
                "quality_grade": "A",
                "sentence_index": 0,
                "word_count": 2
            }
        ]
        
        result = formatter._format_output(mock_results, "csv", False, False)
        
        assert result["success"] == True
        assert "formatted_data" in result
        
        # Check CSV structure
        csv_data = result["formatted_data"]
        lines = csv_data.strip().split('\n')
        assert len(lines) >= 2  # Header + at least one data row
        assert "id,text,approved,quality_grade,word_count" in lines[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
