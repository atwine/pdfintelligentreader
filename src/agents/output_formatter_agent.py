"""
Output Formatter Agent - Specialized in formatting and exporting processed sentences
"""

import json
import csv
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from crewai import Agent
from loguru import logger

from ..config import settings


class OutputFormatterAgent:
    """Agent specialized in formatting and exporting processed sentences"""
    
    def __init__(self):
        self.agent = self._create_agent()
        self.supported_formats = ["json", "csv", "txt", "xml"]
        logger.info("Output Formatter Agent initialized")
    
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent with specialized configuration"""
        return Agent(
            role='Output Formatting Specialist',
            goal='Format and export processed sentences in multiple formats with comprehensive metadata',
            backstory="""You are an expert in data formatting and export systems. You understand 
            the importance of structured output for translation workflows and can format data 
            in multiple formats while preserving all important metadata. Your expertise includes:
            
            - Multi-format export (JSON, CSV, TXT, XML)
            - Metadata preservation and traceability
            - Quality statistics and reporting
            - Batch processing summaries
            - Translation-ready formatting
            - Data validation and integrity checks
            
            You ensure that exported data is properly formatted, complete, and ready 
            for downstream translation processes.""",
            verbose=True,
            allow_delegation=False,
            tools=[self._format_output, self._export_data, self._generate_report]
        )
    
    def _format_output(self, quality_results: List[Dict[str, Any]], output_format: str = "json", 
                      include_metadata: bool = True, approved_only: bool = False) -> Dict[str, Any]:
        """
        Format processed sentences for output
        
        Args:
            quality_results: List of sentences with quality assessment
            output_format: Output format ("json", "csv", "txt", "xml")
            include_metadata: Whether to include processing metadata
            approved_only: Whether to include only approved sentences
            
        Returns:
            Dictionary containing formatted output data
        """
        try:
            logger.info(f"Formatting output in {output_format} format")
            
            if not quality_results:
                return {
                    "success": False,
                    "error": "No data to format",
                    "formatted_data": None
                }
            
            # Filter data if needed
            data_to_format = quality_results
            if approved_only:
                data_to_format = [result for result in quality_results if result.get("approved", False)]
                logger.info(f"Filtered to {len(data_to_format)} approved sentences")
            
            # Format according to specified format
            if output_format.lower() == "json":
                formatted_data = self._format_json(data_to_format, include_metadata)
            elif output_format.lower() == "csv":
                formatted_data = self._format_csv(data_to_format, include_metadata)
            elif output_format.lower() == "txt":
                formatted_data = self._format_txt(data_to_format, include_metadata)
            elif output_format.lower() == "xml":
                formatted_data = self._format_xml(data_to_format, include_metadata)
            else:
                raise ValueError(f"Unsupported format: {output_format}")
            
            # Generate summary statistics
            summary = self._generate_summary(quality_results, data_to_format)
            
            logger.success(f"Successfully formatted {len(data_to_format)} sentences in {output_format} format")
            
            return {
                "success": True,
                "formatted_data": formatted_data,
                "format": output_format,
                "summary": summary,
                "total_sentences": len(quality_results),
                "exported_sentences": len(data_to_format)
            }
            
        except Exception as e:
            error_msg = f"Output formatting error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "formatted_data": None
            }
    
    def _format_json(self, data: List[Dict[str, Any]], include_metadata: bool) -> str:
        """Format data as JSON"""
        output_data = {
            "metadata": {
                "export_timestamp": datetime.utcnow().isoformat(),
                "format": "json",
                "sentence_count": len(data),
                "processing_info": {
                    "min_completeness_threshold": settings.min_sentence_completeness,
                    "min_translation_readiness": settings.min_translation_readiness,
                    "max_noise_threshold": settings.max_noise_threshold
                }
            },
            "sentences": []
        }
        
        for item in data:
            sentence_data = {
                "id": item.get("sentence_index", 0),
                "text": item["text"],
                "approved": item.get("approved", False),
                "quality_grade": item.get("quality_grade", "F")
            }
            
            if include_metadata:
                sentence_data.update({
                    "word_count": item.get("word_count", 0),
                    "char_count": item.get("char_count", 0),
                    "extraction_method": item.get("method", "unknown"),
                    "confidence": item.get("confidence", 0.0),
                    "quality_scores": item.get("quality_scores", {}),
                    "translation_readiness": item.get("translation_readiness", {}),
                    "context_info": {
                        "needs_context": item.get("needs_context", False),
                        "context_score": item.get("context_score", 0.0)
                    },
                    "issues": item.get("issues", [])
                })
            
            output_data["sentences"].append(sentence_data)
        
        return json.dumps(output_data, indent=2, ensure_ascii=False)
    
    def _format_csv(self, data: List[Dict[str, Any]], include_metadata: bool) -> str:
        """Format data as CSV"""
        if not data:
            return ""
        
        # Define CSV columns
        base_columns = ["id", "text", "approved", "quality_grade", "word_count"]
        
        if include_metadata:
            metadata_columns = [
                "char_count", "extraction_method", "confidence",
                "completeness_score", "clarity_score", "structure_score", "content_score",
                "translation_readiness_score", "translation_readiness_level",
                "needs_context", "context_score", "issues_count"
            ]
            columns = base_columns + metadata_columns
        else:
            columns = base_columns
        
        # Create CSV content
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(columns)
        
        # Write data rows
        for item in data:
            row = [
                item.get("sentence_index", 0),
                item["text"],
                item.get("approved", False),
                item.get("quality_grade", "F"),
                item.get("word_count", 0)
            ]
            
            if include_metadata:
                quality_scores = item.get("quality_scores", {})
                translation_readiness = item.get("translation_readiness", {})
                
                row.extend([
                    item.get("char_count", 0),
                    item.get("method", "unknown"),
                    item.get("confidence", 0.0),
                    quality_scores.get("completeness", 0.0),
                    quality_scores.get("clarity", 0.0),
                    quality_scores.get("structure", 0.0),
                    quality_scores.get("content", 0.0),
                    translation_readiness.get("score", 0.0),
                    translation_readiness.get("level", "unknown"),
                    item.get("needs_context", False),
                    item.get("context_score", 0.0),
                    len(item.get("issues", []))
                ])
            
            writer.writerow(row)
        
        return output.getvalue()
    
    def _format_txt(self, data: List[Dict[str, Any]], include_metadata: bool) -> str:
        """Format data as plain text"""
        lines = []
        
        # Header
        lines.append("PDF Intelligent Reader - Extracted Sentences")
        lines.append("=" * 50)
        lines.append(f"Export Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append(f"Total Sentences: {len(data)}")
        lines.append("")
        
        # Sentences
        for i, item in enumerate(data, 1):
            lines.append(f"Sentence {i}:")
            lines.append(f"Text: {item['text']}")
            
            if include_metadata:
                lines.append(f"Approved: {item.get('approved', False)}")
                lines.append(f"Quality Grade: {item.get('quality_grade', 'F')}")
                lines.append(f"Word Count: {item.get('word_count', 0)}")
                
                quality_scores = item.get("quality_scores", {})
                if quality_scores:
                    lines.append(f"Quality Scores: Completeness={quality_scores.get('completeness', 0):.2f}, "
                               f"Clarity={quality_scores.get('clarity', 0):.2f}, "
                               f"Structure={quality_scores.get('structure', 0):.2f}")
                
                translation_readiness = item.get("translation_readiness", {})
                if translation_readiness:
                    lines.append(f"Translation Readiness: {translation_readiness.get('score', 0):.2f} "
                               f"({translation_readiness.get('level', 'unknown')})")
            
            lines.append("-" * 30)
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_xml(self, data: List[Dict[str, Any]], include_metadata: bool) -> str:
        """Format data as XML"""
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append('<pdf_extraction>')
        lines.append(f'  <metadata>')
        lines.append(f'    <export_timestamp>{datetime.utcnow().isoformat()}</export_timestamp>')
        lines.append(f'    <sentence_count>{len(data)}</sentence_count>')
        lines.append(f'  </metadata>')
        lines.append('  <sentences>')
        
        for item in data:
            lines.append(f'    <sentence id="{item.get("sentence_index", 0)}">')
            lines.append(f'      <text><![CDATA[{item["text"]}]]></text>')
            lines.append(f'      <approved>{item.get("approved", False)}</approved>')
            lines.append(f'      <quality_grade>{item.get("quality_grade", "F")}</quality_grade>')
            
            if include_metadata:
                lines.append(f'      <word_count>{item.get("word_count", 0)}</word_count>')
                lines.append(f'      <confidence>{item.get("confidence", 0.0)}</confidence>')
                
                quality_scores = item.get("quality_scores", {})
                if quality_scores:
                    lines.append('      <quality_scores>')
                    for score_type, score_value in quality_scores.items():
                        lines.append(f'        <{score_type}>{score_value}</{score_type}>')
                    lines.append('      </quality_scores>')
            
            lines.append('    </sentence>')
        
        lines.append('  </sentences>')
        lines.append('</pdf_extraction>')
        
        return "\n".join(lines)
    
    def _generate_summary(self, original_data: List[Dict[str, Any]], exported_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate processing summary"""
        total_sentences = len(original_data)
        exported_sentences = len(exported_data)
        
        if total_sentences == 0:
            return {"total_sentences": 0}
        
        # Calculate statistics
        approved_count = sum(1 for item in original_data if item.get("approved", False))
        avg_quality = sum(item.get("overall_quality", {}).get("overall_score", 0) for item in original_data) / total_sentences
        
        grade_distribution = {}
        for item in original_data:
            grade = item.get("quality_grade", "F")
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
        
        return {
            "total_sentences": total_sentences,
            "exported_sentences": exported_sentences,
            "approved_sentences": approved_count,
            "approval_rate": approved_count / total_sentences,
            "average_quality_score": avg_quality,
            "grade_distribution": grade_distribution,
            "export_timestamp": datetime.utcnow().isoformat()
        }
    
    def _export_data(self, formatted_data: str, output_path: str, format_type: str) -> Dict[str, Any]:
        """Tool function for exporting formatted data to file"""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_data)
            
            file_size = output_file.stat().st_size
            
            logger.success(f"Data exported to {output_path} ({file_size} bytes)")
            
            return {
                "success": True,
                "output_path": str(output_path),
                "file_size": file_size,
                "format": format_type
            }
            
        except Exception as e:
            error_msg = f"Export error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    def _generate_report(self, quality_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tool function for generating processing report"""
        if not quality_results:
            return {"error": "No data for report generation"}
        
        # Generate comprehensive report
        report = {
            "processing_summary": self._generate_summary(quality_results, quality_results),
            "quality_analysis": {
                "total_sentences": len(quality_results),
                "approved_sentences": sum(1 for r in quality_results if r.get("approved", False)),
                "quality_distribution": {},
                "common_issues": {}
            },
            "recommendations": []
        }
        
        # Analyze quality distribution
        for result in quality_results:
            grade = result.get("quality_grade", "F")
            report["quality_analysis"]["quality_distribution"][grade] = \
                report["quality_analysis"]["quality_distribution"].get(grade, 0) + 1
        
        # Analyze common issues
        for result in quality_results:
            for issue in result.get("issues", []):
                issue_type = issue["type"]
                report["quality_analysis"]["common_issues"][issue_type] = \
                    report["quality_analysis"]["common_issues"].get(issue_type, 0) + 1
        
        # Generate recommendations
        approval_rate = report["processing_summary"]["approval_rate"]
        if approval_rate < 0.8:
            report["recommendations"].append("Consider improving PDF quality or extraction method")
        if "completeness" in report["quality_analysis"]["common_issues"]:
            report["recommendations"].append("Review sentence boundary detection settings")
        
        return report
    
    def get_agent(self) -> Agent:
        """Get the CrewAI agent instance"""
        return self.agent
    
    def process_and_export(self, quality_results: List[Dict[str, Any]], output_format: str = "json", 
                          output_path: Optional[str] = None, approved_only: bool = False) -> Dict[str, Any]:
        """
        Process and export quality results
        
        Args:
            quality_results: List of sentences with quality assessment
            output_format: Output format
            output_path: Path for output file (optional)
            approved_only: Whether to export only approved sentences
            
        Returns:
            Dictionary containing export results
        """
        # Format the data
        format_result = self._format_output(quality_results, output_format, True, approved_only)
        
        if not format_result["success"]:
            return format_result
        
        # Export to file if path provided
        if output_path:
            export_result = self._export_data(format_result["formatted_data"], output_path, output_format)
            format_result["export_result"] = export_result
        
        return format_result
