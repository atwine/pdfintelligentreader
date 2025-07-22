"""
Sentence Boundary Agent - AI-powered sentence boundary detection and segmentation
"""

import re
from typing import Dict, Any, List, Tuple
from crewai import Agent
from loguru import logger
import openai
import spacy
import nltk
from nltk.tokenize import sent_tokenize

from ..config import settings


class SentenceBoundaryAgent:
    """Agent specialized in intelligent sentence boundary detection"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        self.nlp = None
        self._initialize_nlp()
        self.agent = self._create_agent()
        logger.info("Sentence Boundary Agent initialized")
    
    def _initialize_nlp(self):
        """Initialize spaCy and NLTK components"""
        try:
            # Load spaCy model
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded successfully")
        except OSError:
            logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        try:
            # Download NLTK data if needed
            nltk.download('punkt', quiet=True)
            logger.info("NLTK punkt tokenizer ready")
        except Exception as e:
            logger.warning(f"NLTK initialization warning: {e}")
    
    def _create_agent(self) -> Agent:
        """Create the CrewAI agent with specialized configuration"""
        return Agent(
            role='Sentence Boundary Detection Specialist',
            goal='Accurately identify sentence boundaries and extract complete, coherent sentences suitable for translation',
            backstory="""You are an expert in computational linguistics with deep knowledge of 
            sentence boundary detection. You understand the complexities of natural language 
            processing and can identify sentence boundaries even in challenging contexts. 
            Your expertise includes:
            
            - Statistical sentence segmentation using spaCy and NLTK
            - AI-powered boundary detection using GPT-4
            - Handling abbreviations, numbers, and special cases
            - Context-aware sentence splitting
            - Quality assessment of sentence completeness
            - Preserving semantic coherence for translation
            
            You ensure that every extracted sentence is complete, grammatically sound, 
            and ready for high-quality translation.""",
            verbose=True,
            allow_delegation=False,
            tools=[self._detect_sentence_boundaries, self._validate_sentences, self._ai_boundary_detection]
        )
    
    def _detect_sentence_boundaries(self, text: str, method: str = "hybrid") -> Dict[str, Any]:
        """
        Detect sentence boundaries using multiple methods
        
        Args:
            text: Preprocessed text
            method: Detection method ("nltk", "spacy", "ai", "hybrid")
            
        Returns:
            Dictionary containing detected sentences and metadata
        """
        try:
            logger.info(f"Detecting sentence boundaries using {method} method")
            
            if not text or not text.strip():
                return {
                    "success": False,
                    "error": "Empty input text",
                    "sentences": [],
                    "method": method
                }
            
            sentences = []
            
            if method == "nltk":
                sentences = self._nltk_sentence_detection(text)
            elif method == "spacy":
                sentences = self._spacy_sentence_detection(text)
            elif method == "ai":
                sentences = self._ai_sentence_detection(text)
            elif method == "hybrid":
                sentences = self._hybrid_sentence_detection(text)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            # Validate and clean sentences
            validated_sentences = self._validate_and_clean_sentences(sentences)
            
            logger.success(f"Detected {len(validated_sentences)} sentences using {method}")
            
            return {
                "success": True,
                "sentences": validated_sentences,
                "method": method,
                "sentence_count": len(validated_sentences),
                "avg_sentence_length": sum(len(s["text"]) for s in validated_sentences) / len(validated_sentences) if validated_sentences else 0
            }
            
        except Exception as e:
            error_msg = f"Sentence boundary detection error: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "sentences": [],
                "method": method
            }
    
    def _nltk_sentence_detection(self, text: str) -> List[Dict[str, Any]]:
        """Use NLTK for sentence detection"""
        sentences = sent_tokenize(text)
        return [
            {
                "text": sentence.strip(),
                "confidence": 0.8,
                "method": "nltk",
                "start_pos": text.find(sentence),
                "end_pos": text.find(sentence) + len(sentence)
            }
            for sentence in sentences if sentence.strip()
        ]
    
    def _spacy_sentence_detection(self, text: str) -> List[Dict[str, Any]]:
        """Use spaCy for sentence detection"""
        if not self.nlp:
            return self._nltk_sentence_detection(text)  # Fallback
        
        doc = self.nlp(text)
        sentences = []
        
        for sent in doc.sents:
            sentence_text = sent.text.strip()
            if sentence_text:
                sentences.append({
                    "text": sentence_text,
                    "confidence": 0.85,
                    "method": "spacy",
                    "start_pos": sent.start_char,
                    "end_pos": sent.end_char,
                    "has_root": sent.root.pos_ in ["VERB", "NOUN", "ADJ"]  # Basic completeness check
                })
        
        return sentences
    
    def _ai_sentence_detection(self, text: str) -> List[Dict[str, Any]]:
        """Use AI for intelligent sentence detection"""
        try:
            prompt = f"""
            Please analyze the following text and identify sentence boundaries. 
            Extract complete, coherent sentences that are suitable for translation.
            
            Rules:
            1. Each sentence should be grammatically complete
            2. Preserve context and meaning
            3. Handle abbreviations and special cases correctly
            4. Ensure sentences are translation-ready
            
            Text to analyze:
            {text[:2000]}  # Limit for API
            
            Return the sentences as a JSON array with this format:
            [
                {{"text": "Complete sentence here.", "confidence": 0.95}},
                {{"text": "Another complete sentence.", "confidence": 0.90}}
            ]
            """
            
            response = self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert linguist specializing in sentence boundary detection for translation purposes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            # Parse AI response
            import json
            ai_sentences = json.loads(response.choices[0].message.content)
            
            # Format for consistency
            sentences = []
            for i, sent_data in enumerate(ai_sentences):
                sentences.append({
                    "text": sent_data["text"].strip(),
                    "confidence": sent_data.get("confidence", 0.9),
                    "method": "ai",
                    "start_pos": -1,  # AI doesn't provide positions
                    "end_pos": -1
                })
            
            return sentences
            
        except Exception as e:
            logger.error(f"AI sentence detection failed: {e}")
            return self._spacy_sentence_detection(text)  # Fallback
    
    def _hybrid_sentence_detection(self, text: str) -> List[Dict[str, Any]]:
        """Combine multiple methods for best results"""
        # Start with spaCy as base
        spacy_sentences = self._spacy_sentence_detection(text)
        
        # For complex cases, use AI validation
        if len(text) < 2000 and any(len(s["text"]) > 200 for s in spacy_sentences):
            try:
                ai_sentences = self._ai_sentence_detection(text)
                # Use AI results if they seem more reasonable
                if len(ai_sentences) > 0 and abs(len(ai_sentences) - len(spacy_sentences)) <= 2:
                    return ai_sentences
            except:
                pass
        
        return spacy_sentences
    
    def _validate_and_clean_sentences(self, sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and clean detected sentences"""
        validated = []
        
        for i, sentence in enumerate(sentences):
            text = sentence["text"].strip()
            
            # Skip empty or very short sentences
            if len(text) < 10:
                continue
            
            # Skip sentences that are mostly punctuation or numbers
            alpha_ratio = sum(1 for c in text if c.isalpha()) / len(text)
            if alpha_ratio < 0.5:
                continue
            
            # Basic completeness check
            has_verb = bool(re.search(r'\b(is|are|was|were|have|has|had|do|does|did|will|would|can|could|should|may|might)\b', text.lower()))
            ends_properly = text.rstrip().endswith(('.', '!', '?', ':', ';'))
            
            # Calculate completeness score
            completeness_score = 0.5  # Base score
            if has_verb:
                completeness_score += 0.2
            if ends_properly:
                completeness_score += 0.2
            if len(text) > 20:
                completeness_score += 0.1
            
            validated.append({
                "text": text,
                "confidence": sentence.get("confidence", 0.8),
                "method": sentence.get("method", "unknown"),
                "start_pos": sentence.get("start_pos", -1),
                "end_pos": sentence.get("end_pos", -1),
                "completeness_score": completeness_score,
                "sentence_index": i,
                "word_count": len(text.split()),
                "char_count": len(text)
            })
        
        return validated
    
    def _validate_sentences(self, sentences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tool function for sentence validation"""
        validated = self._validate_and_clean_sentences(sentences)
        return {"validated_sentences": validated}
    
    def _ai_boundary_detection(self, text: str) -> Dict[str, Any]:
        """Tool function for AI-powered boundary detection"""
        sentences = self._ai_sentence_detection(text)
        return {"ai_sentences": sentences}
    
    def get_agent(self) -> Agent:
        """Get the CrewAI agent instance"""
        return self.agent
    
    def process_text(self, text: str, method: str = "hybrid") -> Dict[str, Any]:
        """
        Process text for sentence boundary detection
        
        Args:
            text: Preprocessed text
            method: Detection method to use
            
        Returns:
            Dictionary containing detected sentences and metadata
        """
        return self._detect_sentence_boundaries(text, method)
