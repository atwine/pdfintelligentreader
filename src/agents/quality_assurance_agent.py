"""
Quality Assurance Agent - Specialized in sentence quality assessment and validation
"""

import re
from typing import Dict, Any, List, Tuple
from crewai import Agent
from loguru import logger
import openai
import spacy

from ..config import settings


class QualityAssuranceAgent:
    """Agent specialized in comprehensive quality assessment of extracted sentences"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        self.nlp = None
        self._initialize_nlp()
        self.agent = self._create_agent()
        logger.info("Quality Assurance Agent initialized")
    
    def _initialize_nlp(self):
        """Initialize spaCy for quality analysis"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded for quality assessment")
        except OSError:
            logger.warning("spaCy model not found for quality assessment")
            self.nlp = None
    
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent with specialized configuration"""
        return Agent(
            role='Quality Assurance Specialist',
            goal='Assess sentence quality, completeness, and translation readiness with high precision',
            backstory="""You are an expert in linguistic quality assessment with deep knowledge 
            of what makes sentences suitable for translation. You understand grammar, semantics, 
            and the specific requirements for high-quality translation work. Your expertise includes:
            
            - Multi-dimensional quality scoring (completeness, clarity, structure, content)
            - Translation readiness assessment
            - Noise and artifact detection
            - Grammatical completeness validation
            - Semantic coherence analysis
            - Quality threshold enforcement
            
            You ensure that only sentences meeting the highest quality standards are 
            approved for translation, maintaining the integrity of the translation workflow.""",
            verbose=True,
            allow_delegation=False,
            tools=[self._assess_quality, self._validate_completeness, self._score_translation_readiness]
        )
    
    def _assess_quality(self, sentences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Comprehensive quality assessment of sentences
        
        Args:
            sentences: List of sentences with context analysis
            
        Returns:
            Dictionary containing quality assessment results
        """
        try:
            logger.info(f"Assessing quality for {len(sentences)} sentences")
            
            if not sentences:
                return {
                    "success": False,
                    "error": "No sentences to assess",
                    "quality_results": []
                }
            
            quality_results = []
            
            for sentence in sentences:
                # Multi-dimensional quality assessment
                quality_scores = self._calculate_quality_scores(sentence)
                
                # Translation readiness assessment
                translation_readiness = self._assess_translation_readiness(sentence, quality_scores)
                
                # Issue detection
                issues = self._detect_issues(sentence, quality_scores)
                
                # Overall quality determination
                overall_quality = self._determine_overall_quality(quality_scores, translation_readiness, issues)
                
                quality_result = {
                    **sentence,
                    "quality_scores": quality_scores,
                    "translation_readiness": translation_readiness,
                    "issues": issues,
                    "overall_quality": overall_quality,
                    "approved": overall_quality["approved"],
                    "quality_grade": overall_quality["grade"]
                }
                
                quality_results.append(quality_result)
            
            # Calculate batch quality metrics
            batch_metrics = self._calculate_batch_metrics(quality_results)
            
            logger.success(f"Quality assessment completed. {batch_metrics['approved_count']}/{len(sentences)} sentences approved")
            
            return {
                "success": True,
                "quality_results": quality_results,
                "batch_metrics": batch_metrics,
                "meets_quality_threshold": batch_metrics["approval_rate"] >= settings.min_translation_readiness
            }
            
        except Exception as e:
            error_msg = f"Quality assessment error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "quality_results": sentences  # Return original on error
            }
    
    def _calculate_quality_scores(self, sentence: Dict[str, Any]) -> Dict[str, float]:
        """Calculate multi-dimensional quality scores"""
        text = sentence["text"]
        
        # 1. Completeness Score
        completeness_score = self._score_completeness(text, sentence)
        
        # 2. Clarity Score
        clarity_score = self._score_clarity(text)
        
        # 3. Structure Score
        structure_score = self._score_structure(text)
        
        # 4. Content Score
        content_score = self._score_content(text)
        
        return {
            "completeness": completeness_score,
            "clarity": clarity_score,
            "structure": structure_score,
            "content": content_score
        }
    
    def _score_completeness(self, text: str, sentence: Dict[str, Any]) -> float:
        """Score grammatical and semantic completeness"""
        score = 0.0
        
        # Basic completeness indicators
        has_subject_verb = self._has_subject_verb(text)
        proper_punctuation = text.rstrip().endswith(('.', '!', '?', ':', ';'))
        reasonable_length = 5 <= len(text.split()) <= 100
        capital_start = text[0].isupper() if text else False
        
        # Scoring
        if has_subject_verb:
            score += 0.4
        if proper_punctuation:
            score += 0.2
        if reasonable_length:
            score += 0.2
        if capital_start:
            score += 0.1
        
        # Context completeness (from context analysis)
        context_score = sentence.get("context_score", 0.5)
        score += context_score * 0.1
        
        return min(score, 1.0)
    
    def _score_clarity(self, text: str) -> float:
        """Score readability and clarity"""
        words = text.split()
        if not words:
            return 0.0
        
        score = 0.5  # Base score
        
        # Average word length (optimal: 4-6 characters)
        avg_word_length = sum(len(word) for word in words) / len(words)
        if 4 <= avg_word_length <= 6:
            score += 0.2
        
        # Sentence length (optimal: 10-25 words)
        word_count = len(words)
        if 10 <= word_count <= 25:
            score += 0.2
        elif word_count > 40:
            score -= 0.1  # Penalize very long sentences
        
        # Punctuation balance
        punct_count = sum(1 for char in text if char in '.,!?;:')
        punct_ratio = punct_count / len(text)
        if 0.02 <= punct_ratio <= 0.08:
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_structure(self, text: str) -> float:
        """Score grammatical structure"""
        if not self.nlp:
            return 0.7  # Default score when spaCy unavailable
        
        try:
            doc = self.nlp(text)
            score = 0.0
            
            # Check for basic grammatical elements
            has_noun = any(token.pos_ in ["NOUN", "PROPN"] for token in doc)
            has_verb = any(token.pos_ == "VERB" for token in doc)
            has_determiner = any(token.pos_ == "DET" for token in doc)
            
            if has_noun:
                score += 0.3
            if has_verb:
                score += 0.4
            if has_determiner:
                score += 0.1
            
            # Check dependency structure
            root_count = sum(1 for token in doc if token.dep_ == "ROOT")
            if root_count == 1:  # Exactly one root is ideal
                score += 0.2
            
            return min(score, 1.0)
            
        except Exception:
            return 0.7  # Default on error
    
    def _score_content(self, text: str) -> float:
        """Score content quality and meaningfulness"""
        score = 0.5  # Base score
        
        # Content indicators
        alpha_ratio = sum(1 for char in text if char.isalpha()) / len(text) if text else 0
        digit_ratio = sum(1 for char in text if char.isdigit()) / len(text) if text else 0
        
        # Good alpha content
        if alpha_ratio > 0.7:
            score += 0.2
        
        # Not too many digits (unless it's a technical document)
        if digit_ratio < 0.3:
            score += 0.1
        
        # Check for meaningful content (not just formatting artifacts)
        meaningful_words = len([word for word in text.split() if len(word) > 2 and word.isalpha()])
        if meaningful_words >= 3:
            score += 0.2
        
        return min(score, 1.0)
    
    def _assess_translation_readiness(self, sentence: Dict[str, Any], quality_scores: Dict[str, float]) -> Dict[str, Any]:
        """Assess overall translation readiness"""
        # Weighted average of quality dimensions
        weights = {
            "completeness": 0.35,
            "clarity": 0.25,
            "structure": 0.25,
            "content": 0.15
        }
        
        weighted_score = sum(quality_scores[dim] * weight for dim, weight in weights.items())
        
        # Additional factors
        context_penalty = 0.1 if sentence.get("needs_context", False) else 0.0
        reference_penalty = 0.05 if sentence.get("references", {}).get("needs_context_resolution", False) else 0.0
        
        final_score = max(0.0, weighted_score - context_penalty - reference_penalty)
        
        # Determine readiness level
        if final_score >= 0.9:
            readiness_level = "excellent"
        elif final_score >= 0.8:
            readiness_level = "good"
        elif final_score >= 0.7:
            readiness_level = "acceptable"
        elif final_score >= 0.6:
            readiness_level = "marginal"
        else:
            readiness_level = "poor"
        
        return {
            "score": final_score,
            "level": readiness_level,
            "ready_for_translation": final_score >= settings.min_translation_readiness,
            "confidence": min(sentence.get("confidence", 0.8) + (final_score * 0.2), 1.0)
        }
    
    def _detect_issues(self, sentence: Dict[str, Any], quality_scores: Dict[str, float]) -> List[Dict[str, Any]]:
        """Detect specific quality issues"""
        issues = []
        text = sentence["text"]
        
        # Completeness issues
        if quality_scores["completeness"] < 0.7:
            issues.append({
                "type": "completeness",
                "severity": "high" if quality_scores["completeness"] < 0.5 else "medium",
                "description": "Sentence may be incomplete or fragmented"
            })
        
        # Clarity issues
        if quality_scores["clarity"] < 0.6:
            issues.append({
                "type": "clarity",
                "severity": "medium",
                "description": "Sentence may be unclear or difficult to read"
            })
        
        # Structure issues
        if quality_scores["structure"] < 0.6:
            issues.append({
                "type": "structure",
                "severity": "medium",
                "description": "Sentence may have grammatical structure issues"
            })
        
        # Specific pattern issues
        if len(text.split()) < 5:
            issues.append({
                "type": "length",
                "severity": "high",
                "description": "Sentence too short for meaningful translation"
            })
        
        if not text.rstrip().endswith(('.', '!', '?', ':', ';')):
            issues.append({
                "type": "punctuation",
                "severity": "medium",
                "description": "Sentence lacks proper ending punctuation"
            })
        
        # Context issues
        if sentence.get("needs_context", False):
            issues.append({
                "type": "context",
                "severity": "medium",
                "description": "Sentence may need additional context for translation"
            })
        
        return issues
    
    def _determine_overall_quality(self, quality_scores: Dict[str, float], translation_readiness: Dict[str, Any], issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Determine overall quality and approval status"""
        # Calculate overall score
        overall_score = sum(quality_scores.values()) / len(quality_scores)
        
        # Check approval criteria
        meets_completeness = quality_scores["completeness"] >= settings.min_sentence_completeness
        meets_translation = translation_readiness["ready_for_translation"]
        high_severity_issues = any(issue["severity"] == "high" for issue in issues)
        
        approved = meets_completeness and meets_translation and not high_severity_issues
        
        # Determine grade
        if overall_score >= 0.9 and approved:
            grade = "A"
        elif overall_score >= 0.8 and approved:
            grade = "B"
        elif overall_score >= 0.7 and approved:
            grade = "C"
        else:
            grade = "F"
        
        return {
            "overall_score": overall_score,
            "approved": approved,
            "grade": grade,
            "meets_completeness_threshold": meets_completeness,
            "meets_translation_threshold": meets_translation,
            "has_blocking_issues": high_severity_issues
        }
    
    def _calculate_batch_metrics(self, quality_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate quality metrics for the entire batch"""
        total_count = len(quality_results)
        if total_count == 0:
            return {}
        
        approved_count = sum(1 for result in quality_results if result["approved"])
        avg_overall_score = sum(result["overall_quality"]["overall_score"] for result in quality_results) / total_count
        avg_translation_readiness = sum(result["translation_readiness"]["score"] for result in quality_results) / total_count
        
        grade_distribution = {}
        for result in quality_results:
            grade = result["quality_grade"]
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
        
        return {
            "total_count": total_count,
            "approved_count": approved_count,
            "rejected_count": total_count - approved_count,
            "approval_rate": approved_count / total_count,
            "avg_overall_score": avg_overall_score,
            "avg_translation_readiness": avg_translation_readiness,
            "grade_distribution": grade_distribution,
            "quality_threshold_met": avg_translation_readiness >= settings.min_translation_readiness
        }
    
    def _has_subject_verb(self, text: str) -> bool:
        """Check if sentence has basic subject-verb structure"""
        if not self.nlp:
            # Simple heuristic fallback
            return bool(re.search(r'\b(is|are|was|were|have|has|had|do|does|did|will|would|can|could|should|may|might)\b', text.lower()))
        
        try:
            doc = self.nlp(text)
            has_subject = any(token.dep_ in ["nsubj", "nsubjpass"] for token in doc)
            has_verb = any(token.pos_ == "VERB" for token in doc)
            return has_subject and has_verb
        except:
            return True  # Default to true on error
    
    def _validate_completeness(self, sentence: Dict[str, Any]) -> Dict[str, Any]:
        """Tool function for completeness validation"""
        completeness_score = self._score_completeness(sentence["text"], sentence)
        return {"completeness_score": completeness_score}
    
    def _score_translation_readiness(self, sentence: Dict[str, Any]) -> Dict[str, Any]:
        """Tool function for translation readiness scoring"""
        quality_scores = self._calculate_quality_scores(sentence)
        translation_readiness = self._assess_translation_readiness(sentence, quality_scores)
        return {"translation_readiness": translation_readiness}
    
    def get_agent(self) -> Agent:
        """Get the CrewAI agent instance"""
        return self.agent
    
    def process_sentences(self, sentences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process sentences for quality assessment
        
        Args:
            sentences: List of sentences with context analysis
            
        Returns:
            Dictionary containing quality assessment results
        """
        return self._assess_quality(sentences)
