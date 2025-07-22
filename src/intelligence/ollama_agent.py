#!/usr/bin/env python3
"""
Ollama-based Intelligent Agent for Health Context Sentence Validation
"""

import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import requests
from loguru import logger


@dataclass
class SentenceAnalysis:
    """Analysis result for a sentence"""
    is_meaningful: bool
    is_complete_thought: bool
    has_health_context: bool
    confidence_score: float
    reasoning: str
    category: str  # 'content', 'header', 'reference', 'fragment', 'noise'
    recommended_action: str  # 'keep', 'discard', 'merge_with_next'


class OllamaHealthAgent:
    """Intelligent agent using Ollama for health context validation"""
    
    def __init__(self, model_name: str = "llama3.1:8b", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        
        # Health context keywords and patterns
        self.health_keywords = {
            'diseases': ['disease', 'illness', 'infection', 'syndrome', 'disorder', 'condition'],
            'symptoms': ['fever', 'cough', 'pain', 'headache', 'nausea', 'fatigue', 'symptom'],
            'medical_terms': ['patient', 'treatment', 'diagnosis', 'therapy', 'medication', 'clinical'],
            'public_health': ['surveillance', 'outbreak', 'epidemic', 'prevention', 'health', 'medical'],
            'procedures': ['test', 'examination', 'screening', 'assessment', 'evaluation', 'monitoring']
        }
        
        # Patterns to identify non-content
        self.noise_patterns = [
            r'^[ivx]+\s*$',  # Roman numerals alone
            r'^\d+\s*$',     # Numbers alone
            r'^[A-Z\s]+$',   # All caps (likely headers)
            r'^(LIST OF|TABLE OF|FIGURE|APPENDIX)',  # Table of contents items
            r'^\s*[.]{3,}',  # Dots/leaders
            r'^\s*[-_=]{3,}',  # Lines/separators
        ]
    
    def _call_ollama(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """Call Ollama API with error handling"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.1,  # Low temperature for consistent analysis
                    "top_p": 0.9
                }
            }
            
            response = requests.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '').strip()
            
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            return None
    
    def _quick_filter(self, sentence: str) -> bool:
        """Quick rule-based filtering before AI analysis"""
        
        # Remove extra whitespace
        sentence = sentence.strip()
        
        # Too short or too long
        if len(sentence) < 10 or len(sentence) > 500:
            return False
        
        # Check noise patterns
        for pattern in self.noise_patterns:
            if re.match(pattern, sentence, re.IGNORECASE):
                return False
        
        # Must have at least 3 words
        if len(sentence.split()) < 3:
            return False
        
        # Must contain some alphabetic characters
        if not re.search(r'[a-zA-Z]', sentence):
            return False
        
        return True
    
    def _has_health_context(self, sentence: str) -> tuple[bool, float]:
        """Check if sentence has health/medical context"""
        
        sentence_lower = sentence.lower()
        health_score = 0.0
        
        # Check for health keywords
        for category, keywords in self.health_keywords.items():
            for keyword in keywords:
                if keyword in sentence_lower:
                    health_score += 0.2
        
        # Check for medical patterns
        medical_patterns = [
            r'\b(WHO|CDC|ministry of health|department of health)\b',
            r'\b\d+\s*(mg|ml|dose|tablet|capsule)\b',
            r'\b(patient|case|outbreak|epidemic|pandemic)\b',
            r'\b(surveillance|monitoring|reporting|investigation)\b'
        ]
        
        for pattern in medical_patterns:
            if re.search(pattern, sentence_lower):
                health_score += 0.3
        
        return health_score > 0.3, min(1.0, health_score)
    
    def analyze_sentence(self, sentence: str, context: Dict[str, Any] = None) -> SentenceAnalysis:
        """Analyze a sentence for meaningfulness and health context"""
        
        # Quick filtering first
        if not self._quick_filter(sentence):
            return SentenceAnalysis(
                is_meaningful=False,
                is_complete_thought=False,
                has_health_context=False,
                confidence_score=0.9,
                reasoning="Failed quick filter: too short, noise pattern, or non-alphabetic",
                category="noise",
                recommended_action="discard"
            )
        
        # Check health context
        has_health, health_score = self._has_health_context(sentence)
        
        # Create AI analysis prompt
        prompt = f"""
You are an expert in health document analysis. Analyze this sentence from a health/medical document:

SENTENCE: "{sentence}"

Evaluate:
1. Is this a meaningful, complete thought that conveys useful information?
2. Does it contain substantive health/medical content?
3. Is it suitable for translation (not just headers, page numbers, or fragments)?

Consider:
- Complete sentences with subject and predicate
- Substantive health/medical information
- Actionable or informative content
- Not just navigation elements (headers, page numbers, table of contents)

Respond with JSON:
{{
    "is_meaningful": true/false,
    "is_complete_thought": true/false,
    "has_substantive_content": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "category": "content|header|reference|fragment|noise",
    "action": "keep|discard|merge_with_next"
}}
"""
        
        # Get AI analysis
        ai_response = self._call_ollama(prompt, max_tokens=200)
        
        if ai_response:
            try:
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    ai_analysis = json.loads(json_match.group())
                    
                    return SentenceAnalysis(
                        is_meaningful=ai_analysis.get('is_meaningful', False),
                        is_complete_thought=ai_analysis.get('is_complete_thought', False),
                        has_health_context=has_health or ai_analysis.get('has_substantive_content', False),
                        confidence_score=ai_analysis.get('confidence', 0.5),
                        reasoning=ai_analysis.get('reasoning', 'AI analysis completed'),
                        category=ai_analysis.get('category', 'unknown'),
                        recommended_action=ai_analysis.get('action', 'discard')
                    )
                    
            except Exception as e:
                logger.warning(f"Failed to parse AI response: {e}")
        
        # Fallback analysis if AI fails
        return self._fallback_analysis(sentence, has_health, health_score)
    
    def _fallback_analysis(self, sentence: str, has_health: bool, health_score: float) -> SentenceAnalysis:
        """Fallback rule-based analysis if AI fails"""
        
        sentence_lower = sentence.lower()
        
        # Check if it's likely a header
        if (sentence.isupper() or 
            sentence.startswith(('CHAPTER', 'SECTION', 'APPENDIX', 'TABLE', 'FIGURE')) or
            len(sentence.split()) <= 5):
            return SentenceAnalysis(
                is_meaningful=False,
                is_complete_thought=False,
                has_health_context=has_health,
                confidence_score=0.8,
                reasoning="Appears to be header or navigation element",
                category="header",
                recommended_action="discard"
            )
        
        # Check for complete thought indicators
        has_verb = bool(re.search(r'\b(is|are|was|were|have|has|will|should|must|can|may|do|does|did)\b', sentence_lower))
        has_subject = bool(re.search(r'\b(the|a|an|this|that|these|those|patient|case|health|disease)\b', sentence_lower))
        
        is_complete = has_verb and has_subject and len(sentence.split()) >= 5
        is_meaningful = is_complete and (has_health or health_score > 0.1)
        
        return SentenceAnalysis(
            is_meaningful=is_meaningful,
            is_complete_thought=is_complete,
            has_health_context=has_health,
            confidence_score=0.7,
            reasoning=f"Rule-based analysis: verb={has_verb}, subject={has_subject}, health_context={has_health}",
            category="content" if is_meaningful else "fragment",
            recommended_action="keep" if is_meaningful else "discard"
        )
    
    def batch_analyze(self, sentences: List[str], context: Dict[str, Any] = None) -> List[SentenceAnalysis]:
        """Analyze multiple sentences efficiently"""
        
        results = []
        
        for i, sentence in enumerate(sentences):
            logger.info(f"Analyzing sentence {i+1}/{len(sentences)}")
            
            analysis = self.analyze_sentence(sentence, context)
            results.append(analysis)
            
            # Log interesting cases
            if analysis.is_meaningful:
                logger.debug(f"KEPT: {sentence[:100]}...")
            else:
                logger.debug(f"DISCARDED ({analysis.category}): {sentence[:100]}...")
        
        return results
    
    def filter_sentences(self, sentences: List[str], min_confidence: float = 0.6) -> List[Dict[str, Any]]:
        """Filter sentences and return only meaningful ones with metadata"""
        
        analyses = self.batch_analyze(sentences)
        
        filtered_results = []
        
        for sentence, analysis in zip(sentences, analyses):
            if (analysis.is_meaningful and 
                analysis.is_complete_thought and 
                analysis.confidence_score >= min_confidence and
                analysis.recommended_action == "keep"):
                
                filtered_results.append({
                    'sentence': sentence,
                    'analysis': {
                        'is_meaningful': analysis.is_meaningful,
                        'is_complete_thought': analysis.is_complete_thought,
                        'has_health_context': analysis.has_health_context,
                        'confidence_score': analysis.confidence_score,
                        'reasoning': analysis.reasoning,
                        'category': analysis.category
                    },
                    'metadata': {
                        'length': len(sentence),
                        'word_count': len(sentence.split()),
                        'health_relevant': analysis.has_health_context
                    }
                })
        
        logger.info(f"Filtered {len(sentences)} sentences to {len(filtered_results)} meaningful ones")
        
        return filtered_results


# Test function
def test_ollama_agent():
    """Test the Ollama agent"""
    
    agent = OllamaHealthAgent()
    
    test_sentences = [
        "i LIST OF TABLES",  # Should be discarded
        "REPUBLIC OF UGANDA MINISTRY OF HEALTH National Technical Guidelines for Integrated Disease Surveillance",  # Header, should be discarded
        "Disease surveillance is a critical component of public health systems that enables early detection of outbreaks.",  # Should be kept
        "The patient presented with fever, cough, and difficulty breathing.",  # Should be kept
        "Figure 1.2",  # Should be discarded
        "Health workers should report suspected cases within 24 hours of detection.",  # Should be kept
        "iii",  # Should be discarded
        "Integrated Disease Surveillance and Response (IDSR) is a strategy that promotes the use of a single system to carry out surveillance functions for multiple diseases.",  # Should be kept
    ]
    
    results = agent.filter_sentences(test_sentences)
    
    print("🧠 OLLAMA INTELLIGENT FILTERING TEST")
    print("=" * 50)
    
    for result in results:
        print(f"✅ KEPT: {result['sentence'][:100]}...")
        print(f"   Confidence: {result['analysis']['confidence_score']:.2f}")
        print(f"   Reasoning: {result['analysis']['reasoning']}")
        print()


if __name__ == "__main__":
    test_ollama_agent()
