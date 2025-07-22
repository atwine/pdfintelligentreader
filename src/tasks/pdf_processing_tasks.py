"""
CrewAI task definitions for PDF processing pipeline
"""

from typing import Dict, Any, List
from crewai import Task
from loguru import logger

from ..agents import (
    PDFParserAgent,
    TextPreprocessorAgent,
    SentenceBoundaryAgent,
    ContextAnalyzerAgent,
    QualityAssuranceAgent,
    OutputFormatterAgent
)


class PDFProcessingTasks:
    """Task definitions for the PDF processing pipeline"""
    
    def __init__(self):
        # Initialize agents
        self.pdf_parser = PDFParserAgent()
        self.text_preprocessor = TextPreprocessorAgent()
        self.sentence_boundary = SentenceBoundaryAgent()
        self.context_analyzer = ContextAnalyzerAgent()
        self.quality_assurance = QualityAssuranceAgent()
        self.output_formatter = OutputFormatterAgent()
        
        logger.info("PDF Processing Tasks initialized with all agents")
    
    def create_pdf_extraction_task(self, pdf_path: str) -> Task:
        """Create task for PDF text extraction"""
        return Task(
            description=f"""
            Extract text from the PDF document located at: {pdf_path}
            
            Requirements:
            1. Use the most appropriate extraction method (PyMuPDF, pdfplumber, or OCR)
            2. Ensure high extraction quality and confidence
            3. Provide detailed metadata about the extraction process
            4. Handle any extraction errors gracefully with fallback methods
            5. Return structured data with text content and processing metadata
            
            Success Criteria:
            - Text extraction confidence > 0.7
            - Complete metadata provided
            - Error handling implemented
            """,
            agent=self.pdf_parser.get_agent(),
            expected_output="Dictionary containing extracted text, extraction method, confidence score, processing time, and metadata"
        )
    
    def create_text_preprocessing_task(self, extraction_result: Dict[str, Any]) -> Task:
        """Create task for text preprocessing and cleaning"""
        return Task(
            description=f"""
            Clean and preprocess the extracted text to prepare it for sentence boundary detection.
            
            Input: {extraction_result}
            
            Requirements:
            1. Remove extraction artifacts and formatting noise
            2. Normalize whitespace while preserving paragraph structure
            3. Handle special characters and encoding issues
            4. Detect document language
            5. Maintain text integrity for translation purposes
            6. Provide preprocessing statistics and metadata
            
            Success Criteria:
            - Clean, normalized text output
            - Language detection completed
            - Preprocessing statistics provided
            - Text integrity maintained
            """,
            agent=self.text_preprocessor.get_agent(),
            expected_output="Dictionary containing cleaned text, language detection, and preprocessing statistics"
        )
    
    def create_sentence_boundary_task(self, preprocessing_result: Dict[str, Any]) -> Task:
        """Create task for sentence boundary detection"""
        return Task(
            description=f"""
            Detect sentence boundaries and extract complete, coherent sentences suitable for translation.
            
            Input: {preprocessing_result}
            
            Requirements:
            1. Use hybrid approach combining NLTK, spaCy, and AI methods
            2. Ensure each sentence is grammatically complete
            3. Handle abbreviations and special cases correctly
            4. Preserve context and meaning
            5. Provide confidence scores for each sentence
            6. Validate sentence completeness and coherence
            
            Success Criteria:
            - Complete, coherent sentences extracted
            - High boundary detection confidence (> 0.8)
            - Proper handling of edge cases
            - Translation-ready sentence structure
            """,
            agent=self.sentence_boundary.get_agent(),
            expected_output="Dictionary containing detected sentences with metadata, confidence scores, and validation results"
        )
    
    def create_context_analysis_task(self, sentence_result: Dict[str, Any]) -> Task:
        """Create task for context analysis"""
        return Task(
            description=f"""
            Analyze sentence context, relationships, and semantic coherence for translation readiness.
            
            Input: {sentence_result}
            
            Requirements:
            1. Analyze semantic relationships between sentences
            2. Detect references that might need context resolution
            3. Assess standalone quality of each sentence
            4. Identify sentences requiring additional context
            5. Preserve contextual information for translation
            6. Calculate context dependency scores
            
            Success Criteria:
            - Context relationships identified
            - Reference resolution analysis completed
            - Standalone quality assessment provided
            - Context dependency scores calculated
            """,
            agent=self.context_analyzer.get_agent(),
            expected_output="Dictionary containing context analysis results, reference detection, and standalone quality scores"
        )
    
    def create_quality_assurance_task(self, context_result: Dict[str, Any]) -> Task:
        """Create task for quality assurance and validation"""
        return Task(
            description=f"""
            Perform comprehensive quality assessment of extracted sentences for translation readiness.
            
            Input: {context_result}
            
            Requirements:
            1. Multi-dimensional quality scoring (completeness, clarity, structure, content)
            2. Translation readiness assessment
            3. Issue detection and classification
            4. Quality threshold enforcement
            5. Approval/rejection decisions based on quality criteria
            6. Batch quality metrics calculation
            
            Success Criteria:
            - Quality scores > minimum thresholds
            - Translation readiness > 90%
            - Noise level < 5%
            - Clear approval/rejection decisions
            - Comprehensive quality reporting
            """,
            agent=self.quality_assurance.get_agent(),
            expected_output="Dictionary containing quality assessment results, approval decisions, and batch quality metrics"
        )
    
    def create_output_formatting_task(self, quality_result: Dict[str, Any], output_format: str = "json") -> Task:
        """Create task for output formatting and export"""
        return Task(
            description=f"""
            Format and export the processed sentences in the specified format with comprehensive metadata.
            
            Input: {quality_result}
            Output Format: {output_format}
            
            Requirements:
            1. Format data in the specified output format (JSON, CSV, TXT, XML)
            2. Include comprehensive metadata and traceability information
            3. Generate processing summary and statistics
            4. Ensure data integrity and completeness
            5. Provide export-ready formatted output
            6. Include quality metrics and processing report
            
            Success Criteria:
            - Properly formatted output in specified format
            - Complete metadata preservation
            - Processing summary included
            - Data integrity maintained
            - Export-ready format
            """,
            agent=self.output_formatter.get_agent(),
            expected_output=f"Dictionary containing formatted output in {output_format} format with metadata and processing summary"
        )
    
    def get_sequential_tasks(self, pdf_path: str, output_format: str = "json") -> List[Task]:
        """
        Get the complete sequence of tasks for PDF processing
        
        Args:
            pdf_path: Path to the PDF file to process
            output_format: Desired output format
            
        Returns:
            List of tasks in sequential order
        """
        # Note: In actual CrewAI implementation, task dependencies are handled
        # by the Crew orchestrator. Here we define the logical sequence.
        
        tasks = [
            self.create_pdf_extraction_task(pdf_path),
            # Subsequent tasks will receive input from previous tasks via CrewAI
            self.create_text_preprocessing_task({}),  # Placeholder - actual input from previous task
            self.create_sentence_boundary_task({}),   # Placeholder - actual input from previous task
            self.create_context_analysis_task({}),    # Placeholder - actual input from previous task
            self.create_quality_assurance_task({}),   # Placeholder - actual input from previous task
            self.create_output_formatting_task({}, output_format)  # Placeholder - actual input from previous task
        ]
        
        logger.info(f"Created {len(tasks)} sequential tasks for PDF processing")
        return tasks
