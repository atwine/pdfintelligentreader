"""
CrewAI crew orchestration for PDF processing pipeline
"""

import time
from typing import Dict, Any, Optional
from pathlib import Path
from crewai import Crew, Process
from loguru import logger

from ..tasks.pdf_processing_tasks import PDFProcessingTasks
from ..config import settings


class PDFProcessingCrew:
    """CrewAI crew for orchestrating the PDF processing pipeline"""
    
    def __init__(self):
        self.tasks_manager = PDFProcessingTasks()
        self.crew = None
        self._initialize_crew()
        logger.info("PDF Processing Crew initialized")
    
    def _initialize_crew(self):
        """Initialize the CrewAI crew with agents and configuration"""
        try:
            # Get all agents
            agents = [
                self.tasks_manager.pdf_parser.get_agent(),
                self.tasks_manager.text_preprocessor.get_agent(),
                self.tasks_manager.sentence_boundary.get_agent(),
                self.tasks_manager.context_analyzer.get_agent(),
                self.tasks_manager.quality_assurance.get_agent(),
                self.tasks_manager.output_formatter.get_agent()
            ]
            
            # Create crew with sequential process
            self.crew = Crew(
                agents=agents,
                tasks=[],  # Tasks will be added dynamically
                process=Process.sequential,
                verbose=True,
                memory=True,  # Enable memory for context sharing
                max_rpm=10,   # Rate limiting for API calls
                max_execution_time=settings.processing_timeout
            )
            
            logger.success("CrewAI crew initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize CrewAI crew: {str(e)}")
            raise
    
    def process_pdf(self, pdf_path: str, output_format: str = "json", 
                   output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a PDF document through the complete pipeline
        
        Args:
            pdf_path: Path to the PDF file
            output_format: Desired output format (json, csv, txt, xml)
            output_path: Optional output file path
            
        Returns:
            Dictionary containing processing results and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting PDF processing for: {pdf_path}")
            
            # Validate input
            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            # Create tasks for this specific PDF
            tasks = self.tasks_manager.get_sequential_tasks(pdf_path, output_format)
            
            # Update crew with tasks
            self.crew.tasks = tasks
            
            # Execute the crew
            logger.info("Executing PDF processing crew...")
            result = self.crew.kickoff()
            
            processing_time = time.time() - start_time
            
            # Process the result
            processed_result = self._process_crew_result(result, pdf_path, processing_time)
            
            # Export if output path specified
            if output_path and processed_result.get("success", False):
                export_result = self._export_result(processed_result, output_path, output_format)
                processed_result["export_result"] = export_result
            
            logger.success(f"PDF processing completed in {processing_time:.2f} seconds")
            return processed_result
            
        except Exception as e:
            error_msg = f"PDF processing failed: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "processing_time": time.time() - start_time,
                "pdf_path": pdf_path
            }
    
    def process_batch(self, pdf_paths: list, output_format: str = "json", 
                     output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Process multiple PDF documents
        
        Args:
            pdf_paths: List of PDF file paths
            output_format: Desired output format
            output_dir: Optional output directory
            
        Returns:
            Dictionary containing batch processing results
        """
        start_time = time.time()
        
        logger.info(f"Starting batch processing of {len(pdf_paths)} PDFs")
        
        results = {
            "success": True,
            "total_files": len(pdf_paths),
            "processed_files": 0,
            "failed_files": 0,
            "results": [],
            "batch_summary": {}
        }
        
        for i, pdf_path in enumerate(pdf_paths, 1):
            try:
                logger.info(f"Processing file {i}/{len(pdf_paths)}: {Path(pdf_path).name}")
                
                # Determine output path if directory specified
                output_path = None
                if output_dir:
                    output_filename = f"{Path(pdf_path).stem}_processed.{output_format}"
                    output_path = Path(output_dir) / output_filename
                
                # Process individual PDF
                result = self.process_pdf(pdf_path, output_format, str(output_path) if output_path else None)
                
                if result.get("success", False):
                    results["processed_files"] += 1
                else:
                    results["failed_files"] += 1
                
                results["results"].append({
                    "pdf_path": pdf_path,
                    "result": result,
                    "index": i
                })
                
            except Exception as e:
                logger.error(f"Failed to process {pdf_path}: {str(e)}")
                results["failed_files"] += 1
                results["results"].append({
                    "pdf_path": pdf_path,
                    "result": {"success": False, "error": str(e)},
                    "index": i
                })
        
        # Calculate batch summary
        processing_time = time.time() - start_time
        results["processing_time"] = processing_time
        results["success"] = results["failed_files"] == 0
        results["batch_summary"] = self._calculate_batch_summary(results)
        
        logger.success(f"Batch processing completed: {results['processed_files']}/{results['total_files']} successful")
        return results
    
    def _process_crew_result(self, crew_result: Any, pdf_path: str, processing_time: float) -> Dict[str, Any]:
        """Process and structure the crew execution result"""
        try:
            # CrewAI returns the result from the last task
            # In our case, this should be the formatted output
            
            if isinstance(crew_result, dict):
                processed_result = crew_result
            else:
                # If result is not a dict, try to convert or wrap it
                processed_result = {
                    "formatted_data": str(crew_result),
                    "success": True
                }
            
            # Add processing metadata
            processed_result.update({
                "pdf_path": pdf_path,
                "processing_time": processing_time,
                "timestamp": time.time(),
                "crew_execution": True
            })
            
            return processed_result
            
        except Exception as e:
            logger.error(f"Failed to process crew result: {str(e)}")
            return {
                "success": False,
                "error": f"Result processing failed: {str(e)}",
                "pdf_path": pdf_path,
                "processing_time": processing_time
            }
    
    def _export_result(self, result: Dict[str, Any], output_path: str, output_format: str) -> Dict[str, Any]:
        """Export processing result to file"""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Get formatted data from result
            formatted_data = result.get("formatted_data", "")
            
            if not formatted_data:
                # If no formatted data, create a basic export
                import json
                formatted_data = json.dumps(result, indent=2, default=str)
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_data)
            
            file_size = output_file.stat().st_size
            
            logger.success(f"Result exported to {output_path} ({file_size} bytes)")
            
            return {
                "success": True,
                "output_path": str(output_path),
                "file_size": file_size,
                "format": output_format
            }
            
        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    def _calculate_batch_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics for batch processing"""
        successful_results = [r for r in results["results"] if r["result"].get("success", False)]
        
        if not successful_results:
            return {
                "success_rate": 0.0,
                "avg_processing_time": 0.0,
                "total_sentences": 0,
                "avg_quality_score": 0.0
            }
        
        # Calculate averages
        avg_processing_time = sum(r["result"].get("processing_time", 0) for r in successful_results) / len(successful_results)
        
        # Extract quality metrics if available
        total_sentences = 0
        quality_scores = []
        
        for result in successful_results:
            result_data = result["result"]
            if "summary" in result_data:
                total_sentences += result_data["summary"].get("total_sentences", 0)
                if "average_quality_score" in result_data["summary"]:
                    quality_scores.append(result_data["summary"]["average_quality_score"])
        
        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        return {
            "success_rate": len(successful_results) / results["total_files"],
            "avg_processing_time": avg_processing_time,
            "total_sentences": total_sentences,
            "avg_quality_score": avg_quality_score,
            "successful_files": len(successful_results),
            "failed_files": results["failed_files"]
        }
    
    def get_crew_info(self) -> Dict[str, Any]:
        """Get information about the crew configuration"""
        return {
            "agents_count": len(self.crew.agents) if self.crew else 0,
            "process_type": "sequential",
            "memory_enabled": True,
            "max_rpm": 10,
            "max_execution_time": settings.processing_timeout,
            "agents": [
                {
                    "role": agent.role,
                    "goal": agent.goal,
                    "tools_count": len(agent.tools) if hasattr(agent, 'tools') else 0
                }
                for agent in (self.crew.agents if self.crew else [])
            ]
        }
