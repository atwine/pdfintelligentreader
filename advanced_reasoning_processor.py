#!/usr/bin/env python3
"""
Advanced Multi-Dimensional Reasoning Processor with Paraphrasing
Implements sophisticated sentence analysis, scoring, and paraphrasing for translation workflows
"""

import json
import re
import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests


class AdvancedReasoningAgent:
    """Advanced AI agent with multi-dimensional reasoning and paraphrasing"""
    
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
        self.api_url = "http://localhost:11434/api/generate"
        
        # Multi-dimensional scoring weights
        self.scoring_weights = {
            'context_relevance': 0.25,
            'completeness': 0.25,
            'health_relevance': 0.25,
            'translation_readiness': 0.25
        }
        
        # Health context vocabulary (expanded)
        self.health_keywords = [
            'health', 'disease', 'illness', 'infection', 'syndrome', 'disorder',
            'patient', 'treatment', 'diagnosis', 'therapy', 'medication', 'clinical',
            'surveillance', 'outbreak', 'epidemic', 'pandemic', 'prevention', 'symptom',
            'fever', 'cough', 'pain', 'medical', 'care', 'hospital', 'clinic',
            'WHO', 'CDC', 'ministry', 'public health', 'case', 'investigation',
            'community', 'facility', 'reporting', 'notification', 'response',
            'laboratory', 'specimen', 'testing', 'vaccine', 'immunization',
            'mortality', 'morbidity', 'incidence', 'prevalence', 'transmission'
        ]
        
        # Paraphrasing strategies
        self.paraphrasing_strategies = {
            'formal_medical': 'formal, medical terminology, professional tone',
            'simplified_clarity': 'simplified language, clear and accessible',
            'action_oriented': 'action-focused, practical implementation'
        }
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'approved': 0,
            'rejected': 0,
            'paraphrases_generated': 0,
            'avg_processing_time': 0,
            'total_processing_time': 0
        }
    
    def analyze_sentence_advanced(self, sentence: str, show_details: bool = True) -> Dict[str, Any]:
        """Advanced multi-dimensional analysis with paraphrasing"""
        
        start_time = time.time()
        self.stats['total_processed'] += 1
        
        if show_details:
            print(f"\n🧠 ADVANCED ANALYSIS #{self.stats['total_processed']}")
            print(f"   📝 Text: '{sentence[:80]}...'")
        
        # Multi-dimensional scoring
        scores = self._calculate_multi_dimensional_scores(sentence)
        
        # Overall decision based on weighted scores
        overall_score = sum(scores[key] * self.scoring_weights[key] for key in scores)
        approved = overall_score >= 0.7  # Higher threshold for quality
        
        if show_details:
            print(f"   📊 Scores: Context={scores['context_relevance']:.2f}, "
                  f"Complete={scores['completeness']:.2f}, "
                  f"Health={scores['health_relevance']:.2f}, "
                  f"Translation={scores['translation_readiness']:.2f}")
            print(f"   🎯 Overall Score: {overall_score:.2f} ({'APPROVED' if approved else 'REJECTED'})")
        
        result = {
            'sentence': sentence,
            'approved': approved,
            'overall_score': overall_score,
            'dimensional_scores': scores,
            'reasoning': self._generate_reasoning(sentence, scores, approved),
            'paraphrases': {},
            'processing_time': 0
        }
        
        # Generate paraphrases for approved sentences
        if approved:
            self.stats['approved'] += 1
            if show_details:
                print(f"   🔄 Generating paraphrases...")
            
            paraphrases = self._generate_paraphrases(sentence)
            result['paraphrases'] = paraphrases
            self.stats['paraphrases_generated'] += len(paraphrases)
            
            if show_details and paraphrases:
                for style, variant in paraphrases.items():
                    print(f"      {style}: {variant}")
        else:
            self.stats['rejected'] += 1
        
        # Update timing
        processing_time = time.time() - start_time
        result['processing_time'] = processing_time
        self.stats['total_processing_time'] += processing_time
        self.stats['avg_processing_time'] = self.stats['total_processing_time'] / self.stats['total_processed']
        
        if show_details:
            print(f"   ⏱️ Processing time: {processing_time:.2f}s")
        
        return result
    
    def _calculate_multi_dimensional_scores(self, sentence: str) -> Dict[str, float]:
        """Calculate scores across multiple dimensions"""
        
        scores = {}
        
        # 1. Context Relevance (0.0 - 1.0)
        scores['context_relevance'] = self._score_context_relevance(sentence)
        
        # 2. Completeness (0.0 - 1.0)
        scores['completeness'] = self._score_completeness(sentence)
        
        # 3. Health Relevance (0.0 - 1.0)
        scores['health_relevance'] = self._score_health_relevance(sentence)
        
        # 4. Translation Readiness (0.0 - 1.0)
        scores['translation_readiness'] = self._score_translation_readiness(sentence)
        
        return scores
    
    def _score_context_relevance(self, sentence: str) -> float:
        """Score contextual relevance and meaningfulness"""
        
        # Check for complete thoughts
        has_subject = bool(re.search(r'\b(the|a|an|this|that|these|those|patient|case|health|disease|surveillance|community|facility)\b', sentence.lower()))
        has_verb = bool(re.search(r'\b(is|are|was|were|have|has|will|should|must|can|may|do|does|did|include|provide|ensure|establish|implement)\b', sentence.lower()))
        has_object = len(sentence.split()) > 5
        
        # Avoid navigation elements
        is_navigation = bool(re.match(r'^\s*[ivx\d]+\s*[.\s]*[A-Z\s]+\s*[.]+\s*$', sentence, re.IGNORECASE))
        is_header = sentence.isupper() and len(sentence.split()) <= 8
        
        base_score = 0.0
        if has_subject: base_score += 0.3
        if has_verb: base_score += 0.3
        if has_object: base_score += 0.2
        
        # Penalties
        if is_navigation: base_score -= 0.5
        if is_header: base_score -= 0.3
        
        return max(0.0, min(1.0, base_score))
    
    def _score_completeness(self, sentence: str) -> float:
        """Score grammatical and semantic completeness"""
        
        # Length and structure checks
        word_count = len(sentence.split())
        char_count = len(sentence.strip())
        
        # Optimal ranges
        word_score = 1.0 if 8 <= word_count <= 40 else max(0.0, 1.0 - abs(word_count - 20) / 30)
        char_score = 1.0 if 50 <= char_count <= 300 else max(0.0, 1.0 - abs(char_count - 150) / 200)
        
        # Grammar indicators
        proper_capitalization = sentence[0].isupper() if sentence else False
        proper_ending = sentence.endswith(('.', '!', '?', ':')) if sentence else False
        
        grammar_score = 0.0
        if proper_capitalization: grammar_score += 0.5
        if proper_ending: grammar_score += 0.5
        
        return (word_score * 0.4 + char_score * 0.3 + grammar_score * 0.3)
    
    def _score_health_relevance(self, sentence: str) -> float:
        """Score relevance to health/medical domain"""
        
        sentence_lower = sentence.lower()
        found_keywords = [kw for kw in self.health_keywords if kw in sentence_lower]
        
        # Base score from keyword density
        keyword_score = min(1.0, len(found_keywords) * 0.2)
        
        # Bonus for specific health contexts
        health_contexts = [
            'surveillance', 'outbreak', 'epidemic', 'disease', 'health',
            'patient', 'clinical', 'medical', 'treatment', 'diagnosis'
        ]
        
        context_bonus = 0.0
        for context in health_contexts:
            if context in sentence_lower:
                context_bonus += 0.1
        
        return min(1.0, keyword_score + context_bonus)
    
    def _score_translation_readiness(self, sentence: str) -> float:
        """Score suitability for professional translation"""
        
        # Clear, unambiguous language
        clarity_score = 1.0
        
        # Avoid abbreviations without context
        abbrev_pattern = r'\b[A-Z]{2,}\b'
        abbreviations = re.findall(abbrev_pattern, sentence)
        if len(abbreviations) > 3:
            clarity_score -= 0.3
        
        # Avoid incomplete references
        incomplete_refs = bool(re.search(r'\.\.\.\.|see\s+\w+|refer\s+to|as\s+mentioned', sentence.lower()))
        if incomplete_refs:
            clarity_score -= 0.4
        
        # Prefer active voice and clear structure
        passive_indicators = ['is done', 'are made', 'was established', 'were implemented']
        has_passive = any(indicator in sentence.lower() for indicator in passive_indicators)
        if has_passive:
            clarity_score -= 0.1
        
        return max(0.0, clarity_score)
    
    def _generate_reasoning(self, sentence: str, scores: Dict[str, float], approved: bool) -> str:
        """Generate human-readable reasoning for the decision"""
        
        reasoning_parts = []
        
        # Context analysis
        if scores['context_relevance'] >= 0.7:
            reasoning_parts.append("Strong contextual relevance")
        elif scores['context_relevance'] >= 0.4:
            reasoning_parts.append("Moderate contextual relevance")
        else:
            reasoning_parts.append("Low contextual relevance")
        
        # Completeness analysis
        if scores['completeness'] >= 0.8:
            reasoning_parts.append("well-structured and complete")
        elif scores['completeness'] >= 0.5:
            reasoning_parts.append("reasonably complete")
        else:
            reasoning_parts.append("incomplete or poorly structured")
        
        # Health relevance
        if scores['health_relevance'] >= 0.6:
            reasoning_parts.append("strong health domain relevance")
        elif scores['health_relevance'] >= 0.3:
            reasoning_parts.append("some health relevance")
        else:
            reasoning_parts.append("limited health relevance")
        
        # Translation readiness
        if scores['translation_readiness'] >= 0.7:
            reasoning_parts.append("excellent translation readiness")
        elif scores['translation_readiness'] >= 0.5:
            reasoning_parts.append("good translation readiness")
        else:
            reasoning_parts.append("poor translation readiness")
        
        decision = "APPROVED" if approved else "REJECTED"
        return f"{decision}: {', '.join(reasoning_parts)}"
    
    def _generate_paraphrases(self, sentence: str) -> Dict[str, str]:
        """Generate paraphrased variants using different strategies"""
        
        paraphrases = {}
        
        for strategy_name, strategy_desc in self.paraphrasing_strategies.items():
            try:
                paraphrase = self._generate_single_paraphrase(sentence, strategy_desc)
                if paraphrase and paraphrase != sentence:
                    paraphrases[strategy_name] = paraphrase
            except Exception as e:
                print(f"      ⚠️ Paraphrasing failed for {strategy_name}: {e}")
                continue
        
        return paraphrases
    
    def _generate_single_paraphrase(self, sentence: str, strategy: str) -> Optional[str]:
        """Generate a single paraphrase using Ollama"""
        
        prompt = f"""Paraphrase the following sentence using a {strategy} style:

Original: "{sentence}"

Requirements:
- Maintain the exact same meaning and information
- Use {strategy} approach
- Keep it suitable for professional translation
- Make it clear and unambiguous
- Ensure proper grammar and structure

Paraphrased version:"""
        
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 100}
            }
            
            response = requests.post(self.api_url, json=payload, timeout=15)
            
            if response.status_code == 200:
                result = response.json().get('response', '').strip()
                
                # Clean up the response
                result = re.sub(r'^(Paraphrased version:|Paraphrase:)\s*', '', result, flags=re.IGNORECASE)
                result = result.strip('"\'')
                
                # Validate the paraphrase
                if len(result) > 10 and result != sentence:
                    return result
            
        except Exception as e:
            print(f"      ⚠️ Ollama request failed: {e}")
        
        return None
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        
        approval_rate = (self.stats['approved'] / self.stats['total_processed']) * 100 if self.stats['total_processed'] > 0 else 0
        paraphrase_rate = (self.stats['paraphrases_generated'] / self.stats['approved']) if self.stats['approved'] > 0 else 0
        
        return {
            'total_processed': self.stats['total_processed'],
            'approved': self.stats['approved'],
            'rejected': self.stats['rejected'],
            'approval_rate': f"{approval_rate:.1f}%",
            'paraphrases_generated': self.stats['paraphrases_generated'],
            'avg_paraphrases_per_sentence': f"{paraphrase_rate:.1f}",
            'avg_processing_time': f"{self.stats['avg_processing_time']:.2f}s",
            'total_processing_time': f"{self.stats['total_processing_time']:.1f}s"
        }


def process_pdf_with_advanced_reasoning(pdf_path: str, max_sentences: int = None, verbose: bool = True) -> Dict[str, Any]:
    """Process PDF with advanced reasoning and paraphrasing"""
    
    print(f"\n🧠 ADVANCED REASONING PROCESSOR")
    print(f"📄 Processing: {os.path.basename(pdf_path)}")
    print("=" * 60)
    
    # Import text extraction from enhanced processor
    try:
        from enhanced_intelligent_processor import extract_text, preprocess_text
    except ImportError:
        print("❌ Could not import text processing functions")
        return {"error": "Missing dependencies"}
    
    # Extract and preprocess text
    text = extract_text(pdf_path)
    if not text:
        return {"error": "No text extracted"}
    
    sentences = preprocess_text(text)
    if max_sentences:
        sentences = sentences[:max_sentences]
    
    print(f"📝 Processing {len(sentences)} sentences with advanced reasoning...")
    
    # Initialize advanced agent
    agent = AdvancedReasoningAgent()
    
    # Process sentences
    results = []
    for i, sentence in enumerate(sentences, 1):
        analysis = agent.analyze_sentence_advanced(sentence, show_details=verbose)
        results.append(analysis)
        
        # Show progress every 10 sentences
        if not verbose and i % 10 == 0:
            stats = agent.get_processing_stats()
            print(f"   Progress: {i}/{len(sentences)} | Approved: {stats['approved']} | Paraphrases: {stats['paraphrases_generated']}")
    
    # Final statistics
    final_stats = agent.get_processing_stats()
    
    print(f"\n🎉 ADVANCED PROCESSING COMPLETE!")
    print(f"   📊 Total processed: {final_stats['total_processed']}")
    print(f"   ✅ Approved: {final_stats['approved']} ({final_stats['approval_rate']})")
    print(f"   🔄 Paraphrases generated: {final_stats['paraphrases_generated']}")
    print(f"   ⏱️ Avg processing time: {final_stats['avg_processing_time']}")
    
    # Save results
    output_file = f"output/{os.path.splitext(os.path.basename(pdf_path))[0]}_advanced_reasoning.json"
    os.makedirs("output", exist_ok=True)
    
    output_data = {
        'metadata': {
            'processed_at': datetime.now().isoformat(),
            'source_file': pdf_path,
            'processor': 'advanced_reasoning',
            'total_sentences': len(sentences),
            'processing_stats': final_stats
        },
        'sentences': results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Results saved to: {output_file}")
    
    return output_data


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python advanced_reasoning_processor.py <pdf_file> [max_sentences]")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    max_sentences = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if not os.path.exists(pdf_file):
        print(f"❌ File not found: {pdf_file}")
        sys.exit(1)
    
    process_pdf_with_advanced_reasoning(pdf_file, max_sentences, verbose=True)
