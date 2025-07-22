"""
Context Analyzer Agent - Specialized in analyzing sentence context and relationships
"""

from typing import Dict, Any, List, Optional
from crewai import Agent
from loguru import logger
import openai
import spacy

from ..config import settings


class ContextAnalyzerAgent:
    """Agent specialized in context analysis and sentence relationship detection"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        self.nlp = None
        self._initialize_nlp()
        self.agent = self._create_agent()
        logger.info("Context Analyzer Agent initialized")
    
    def _initialize_nlp(self):
        """Initialize spaCy for context analysis"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded for context analysis")
        except OSError:
            logger.warning("spaCy model not found for context analysis")
            self.nlp = None
    
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent with specialized configuration"""
        return Agent(
            role='Context Analysis Specialist',
            goal='Analyze sentence context, preserve semantic relationships, and ensure translation readiness',
            backstory="""You are an expert in computational semantics and discourse analysis. 
            You understand how sentences relate to each other within documents and can identify 
            context that is crucial for accurate translation. Your expertise includes:
            
            - Semantic relationship analysis between sentences
            - Discourse coherence and cohesion analysis
            - Reference resolution (pronouns, anaphora)
            - Context preservation for translation accuracy
            - Identifying sentences that require additional context
            - Detecting incomplete or fragmented content
            
            You ensure that extracted sentences maintain their semantic integrity and 
            provide sufficient context for accurate translation.""",
            verbose=True,
            allow_delegation=False,
            tools=[self._analyze_context, self._detect_references, self._assess_translation_context]
        )
    
    def _analyze_context(self, sentences: List[Dict[str, Any]], preserve_context: bool = True) -> Dict[str, Any]:
        """
        Analyze context and relationships between sentences
        
        Args:
            sentences: List of detected sentences with metadata
            preserve_context: Whether to preserve contextual information
            
        Returns:
            Dictionary containing context analysis results
        """
        try:
            logger.info(f"Analyzing context for {len(sentences)} sentences")
            
            if not sentences:
                return {
                    "success": False,
                    "error": "No sentences to analyze",
                    "analyzed_sentences": []
                }
            
            analyzed_sentences = []
            
            for i, sentence in enumerate(sentences):
                # Get surrounding context
                context_before = self._get_context_before(sentences, i)
                context_after = self._get_context_after(sentences, i)
                
                # Analyze sentence dependencies
                dependencies = self._analyze_dependencies(sentence["text"])
                
                # Detect references
                references = self._detect_references_internal(sentence["text"], context_before)
                
                # Calculate context score
                context_score = self._calculate_context_score(sentence, dependencies, references)
                
                analyzed_sentence = {
                    **sentence,
                    "context_before": context_before,
                    "context_after": context_after,
                    "dependencies": dependencies,
                    "references": references,
                    "context_score": context_score,
                    "needs_context": context_score < 0.7,
                    "standalone_quality": self._assess_standalone_quality(sentence["text"])
                }
                
                analyzed_sentences.append(analyzed_sentence)
            
            # Calculate overall context metrics
            context_metrics = self._calculate_context_metrics(analyzed_sentences)
            
            logger.success(f"Context analysis completed. {context_metrics['sentences_needing_context']} sentences need additional context")
            
            return {
                "success": True,
                "analyzed_sentences": analyzed_sentences,
                "context_metrics": context_metrics
            }
            
        except Exception as e:
            error_msg = f"Context analysis error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "analyzed_sentences": sentences  # Return original on error
            }
    
    def _get_context_before(self, sentences: List[Dict[str, Any]], index: int, window: int = 2) -> str:
        """Get context sentences before the current sentence"""
        start_idx = max(0, index - window)
        context_sentences = [s["text"] for s in sentences[start_idx:index]]
        return " ".join(context_sentences)
    
    def _get_context_after(self, sentences: List[Dict[str, Any]], index: int, window: int = 1) -> str:
        """Get context sentences after the current sentence"""
        end_idx = min(len(sentences), index + window + 1)
        context_sentences = [s["text"] for s in sentences[index + 1:end_idx]]
        return " ".join(context_sentences)
    
    def _analyze_dependencies(self, text: str) -> Dict[str, Any]:
        """Analyze grammatical dependencies in the sentence"""
        if not self.nlp:
            return {"has_dependencies": False, "dependency_count": 0}
        
        try:
            doc = self.nlp(text)
            
            # Count different types of dependencies
            dep_counts = {}
            for token in doc:
                dep = token.dep_
                dep_counts[dep] = dep_counts.get(dep, 0) + 1
            
            # Check for important dependency types
            has_subject = any(dep in ["nsubj", "nsubjpass"] for dep in dep_counts)
            has_object = any(dep in ["dobj", "pobj", "iobj"] for dep in dep_counts)
            has_verb = any(token.pos_ == "VERB" for token in doc)
            
            return {
                "has_dependencies": len(dep_counts) > 0,
                "dependency_count": len(dep_counts),
                "dependency_types": list(dep_counts.keys()),
                "has_subject": has_subject,
                "has_object": has_object,
                "has_verb": has_verb,
                "grammatical_completeness": (has_subject + has_object + has_verb) / 3.0
            }
            
        except Exception as e:
            logger.warning(f"Dependency analysis failed: {e}")
            return {"has_dependencies": False, "dependency_count": 0}
    
    def _detect_references_internal(self, text: str, context: str) -> Dict[str, Any]:
        """Detect references that might need context"""
        import re
        
        # Detect pronouns
        pronouns = re.findall(r'\b(he|she|it|they|this|that|these|those|which|who|whom)\b', text.lower())
        
        # Detect demonstratives
        demonstratives = re.findall(r'\b(this|that|these|those|such|said)\b', text.lower())
        
        # Detect incomplete references
        incomplete_refs = re.findall(r'\b(the above|the following|as mentioned|aforementioned)\b', text.lower())
        
        # Calculate reference density
        total_words = len(text.split())
        reference_density = (len(pronouns) + len(demonstratives) + len(incomplete_refs)) / total_words if total_words > 0 else 0
        
        return {
            "pronouns": pronouns,
            "demonstratives": demonstratives,
            "incomplete_references": incomplete_refs,
            "reference_density": reference_density,
            "needs_context_resolution": reference_density > 0.1 or len(incomplete_refs) > 0
        }
    
    def _calculate_context_score(self, sentence: Dict[str, Any], dependencies: Dict[str, Any], references: Dict[str, Any]) -> float:
        """Calculate how well the sentence stands alone"""
        score = 0.5  # Base score
        
        # Grammatical completeness
        if dependencies.get("grammatical_completeness", 0) > 0.8:
            score += 0.3
        
        # Reference resolution
        if not references.get("needs_context_resolution", True):
            score += 0.2
        
        # Sentence length (reasonable length indicates completeness)
        word_count = sentence.get("word_count", 0)
        if 10 <= word_count <= 50:
            score += 0.1
        
        # Ends properly
        if sentence["text"].rstrip().endswith(('.', '!', '?')):
            score += 0.1
        
        return min(score, 1.0)
    
    def _assess_standalone_quality(self, text: str) -> Dict[str, Any]:
        """Assess how well the sentence stands alone for translation"""
        word_count = len(text.split())
        char_count = len(text)
        
        # Basic quality indicators
        has_proper_ending = text.rstrip().endswith(('.', '!', '?'))
        has_capital_start = text[0].isupper() if text else False
        reasonable_length = 10 <= word_count <= 100
        
        # Calculate standalone score
        standalone_score = 0.0
        if has_proper_ending:
            standalone_score += 0.3
        if has_capital_start:
            standalone_score += 0.2
        if reasonable_length:
            standalone_score += 0.3
        if word_count >= 5:
            standalone_score += 0.2
        
        return {
            "standalone_score": standalone_score,
            "has_proper_ending": has_proper_ending,
            "has_capital_start": has_capital_start,
            "reasonable_length": reasonable_length,
            "word_count": word_count,
            "char_count": char_count
        }
    
    def _calculate_context_metrics(self, analyzed_sentences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall context metrics"""
        total_sentences = len(analyzed_sentences)
        if total_sentences == 0:
            return {}
        
        sentences_needing_context = sum(1 for s in analyzed_sentences if s.get("needs_context", False))
        avg_context_score = sum(s.get("context_score", 0) for s in analyzed_sentences) / total_sentences
        avg_standalone_score = sum(s.get("standalone_quality", {}).get("standalone_score", 0) for s in analyzed_sentences) / total_sentences
        
        return {
            "total_sentences": total_sentences,
            "sentences_needing_context": sentences_needing_context,
            "context_dependency_rate": sentences_needing_context / total_sentences,
            "avg_context_score": avg_context_score,
            "avg_standalone_score": avg_standalone_score,
            "high_quality_sentences": sum(1 for s in analyzed_sentences if s.get("context_score", 0) > 0.8)
        }
    
    def _detect_references(self, text: str, context: str = "") -> Dict[str, Any]:
        """Tool function for reference detection"""
        return self._detect_references_internal(text, context)
    
    def _assess_translation_context(self, sentences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tool function for assessing translation context needs"""
        try:
            # Use AI to assess translation context needs
            if len(sentences) > 5:  # Only for larger sets
                sample_text = "\n".join([s["text"] for s in sentences[:5]])
                
                prompt = f"""
                Analyze these sentences for translation readiness. Identify which sentences 
                might need additional context for accurate translation:
                
                {sample_text}
                
                Return a JSON object with translation context assessment.
                """
                
                response = self.openai_client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[
                        {"role": "system", "content": "You are a translation expert analyzing context needs."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
                
                return {"ai_assessment": response.choices[0].message.content}
            
            return {"ai_assessment": "Sample too small for AI analysis"}
            
        except Exception as e:
            return {"ai_assessment": f"AI analysis failed: {str(e)}"}
    
    def get_agent(self) -> Agent:
        """Get the CrewAI agent instance"""
        return self.agent
    
    def process_sentences(self, sentences: List[Dict[str, Any]], preserve_context: bool = True) -> Dict[str, Any]:
        """
        Process sentences for context analysis
        
        Args:
            sentences: List of detected sentences
            preserve_context: Whether to preserve contextual information
            
        Returns:
            Dictionary containing context analysis results
        """
        return self._analyze_context(sentences, preserve_context)
