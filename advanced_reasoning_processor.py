#!/usr/bin/env python3
"""
Advanced Multi-Dimensional Reasoning PDF Processor with Paraphrasing
Enhanced intelligence system for translation-ready content generation
"""

import json
import re
import requests
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pdfplumber
import fitz  # PyMuPDF

class AdvancedReasoningProcessor:
    """Advanced PDF processor with multi-dimensional reasoning and paraphrasing"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434/api/generate"):
        self.ollama_url = ollama_url
        self.model = "llama3.1:8b"
        
        # Enhanced health keywords
        self.health_keywords = [
            'surveillance', 'outbreak', 'epidemic', 'pandemic', 'disease', 'infection',
            'transmission', 'diagnosis', 'treatment', 'therapy', 'clinical', 'patient',
            'prevention', 'immunization', 'vaccination', 'health', 'medical', 'hospital'
        ]
        
        # Noise patterns
        self.noise_patterns = [
            r'^[ivxlcdm]+$', r'^\d+$', r'^[a-z]$', r'^figure \d+', r'^table \d+',
            r'^page \d+', r'^chapter \d+', r'^\d+\.\d+$', r'^list of', r'^appendix'
        ]
    
    def process_pdf(self, pdf_path: str, detail_level: str = "full") -> Dict:
        """Process PDF with advanced reasoning and paraphrasing"""
        
        print(f"\n🧠 ADVANCED REASONING PDF PROCESSOR")
        print(f"📄 Processing: {pdf_path}")
        print("=" * 60)
        
        start_time = time.time()
        
        # Extract and process
        raw_text = self._extract_text_from_pdf(pdf_path)
        sentences = self._split_into_sentences(raw_text)
        print(f"📝 Found {len(sentences)} potential sentences")
        
        results = {
            'metadata': {
                'processed_at': datetime.now().isoformat(),
                'total_raw_sentences': len(sentences),
                'processing_model': self.model
            },
            'approved_sentences': [],
            'rejected_sentences': []
        }
        
        # Process each sentence
        for i, sentence in enumerate(sentences, 1):
            if detail_level == "full":
                print(f"\n📝 [{i}/{len(sentences)}] Analyzing: {sentence[:60]}...")
            
            analysis = self._advanced_reasoning_pipeline(sentence)
            
            if analysis['approved']:
                results['approved_sentences'].append(analysis)
                if detail_level == "full":
                    print(f"✅ APPROVED (confidence: {analysis['confidence']:.2f})")
                    print(f"   Paraphrases: {len(analysis['paraphrases'])}")
            else:
                results['rejected_sentences'].append(analysis)
                if detail_level == "full":
                    print(f"❌ REJECTED: {analysis['rejection_reason']}")
        
        processing_time = time.time() - start_time
        print(f"\n🎉 PROCESSING COMPLETE! Time: {processing_time:.1f}s")
        print(f"✅ Approved: {len(results['approved_sentences'])}/{len(sentences)}")
        
        return results
    
    def _advanced_reasoning_pipeline(self, sentence: str) -> Dict:
        """Multi-dimensional reasoning with paraphrasing"""
        
        # Quick filter
        quick_pass, quick_reason = self._quick_filter(sentence)
        if not quick_pass:
            return {
                'approved': False,
                'original': sentence,
                'rejection_reason': f"Quick filter: {quick_reason}"
            }
        
        # Multi-dimensional analysis
        reasoning_results = {
            'context_analysis': self._analyze_context(sentence),
            'linguistic_quality': self._assess_linguistic_quality(sentence),
            'content_value': self._evaluate_content_value(sentence),
            'translation_readiness': self._assess_translation_readiness(sentence)
        }
        
        # Weighted decision
        approval_score = self._calculate_weighted_score(reasoning_results)
        
        if approval_score >= 0.7:  # Approved
            paraphrases = self._generate_paraphrases(sentence)
            
            return {
                'approved': True,
                'original': sentence,
                'reasoning': reasoning_results,
                'confidence': approval_score,
                'paraphrases': paraphrases,
                'analysis_method': 'advanced_multi_dimensional'
            }
        
        return {
            'approved': False,
            'original': sentence,
            'reasoning': reasoning_results,
            'rejection_reason': self._get_primary_rejection_reason(reasoning_results),
            'confidence': approval_score
        }
    
    def _analyze_context(self, sentence: str) -> Dict:
        """Analyze contextual relevance"""
        domain_score = self._check_health_domain(sentence)
        completeness_score = self._assess_completeness(sentence)
        coherence_score = self._check_logical_flow(sentence)
        
        return {
            'domain_relevance': domain_score,
            'completeness': completeness_score,
            'coherence': coherence_score,
            'overall_score': (domain_score + completeness_score + coherence_score) / 3
        }
    
    def _assess_linguistic_quality(self, sentence: str) -> Dict:
        """Assess linguistic quality"""
        grammar_score = self._check_grammar(sentence)
        clarity_score = self._assess_clarity(sentence)
        readability_score = self._calculate_readability(sentence)
        
        return {
            'grammar_score': grammar_score,
            'clarity_score': clarity_score,
            'readability': readability_score,
            'overall_score': (grammar_score + clarity_score + readability_score) / 3
        }
    
    def _evaluate_content_value(self, sentence: str) -> Dict:
        """Evaluate content value"""
        info_density = self._calculate_information_density(sentence)
        actionability_score = self._assess_actionability(sentence)
        
        return {
            'information_density': info_density,
            'actionability': actionability_score,
            'overall_score': (info_density + actionability_score) / 2
        }
    
    def _assess_translation_readiness(self, sentence: str) -> Dict:
        """Assess translation readiness"""
        cultural_score = self._assess_cultural_transferability(sentence)
        terminology_score = self._assess_terminology_usage(sentence)
        ambiguity_score = 1.0 - self._assess_ambiguity(sentence)
        
        return {
            'cultural_transferability': cultural_score,
            'terminology_usage': terminology_score,
            'ambiguity_score': ambiguity_score,
            'overall_score': (cultural_score + terminology_score + ambiguity_score) / 3
        }
    
    def _generate_paraphrases(self, sentence: str) -> List[Dict]:
        """Generate paraphrases using different strategies"""
        strategies = [
            ('formal_medical', 'Professional medical language'),
            ('simplified_clarity', 'Clearer, simpler structure'),
            ('action_oriented', 'Emphasize actionable elements')
        ]
        
        paraphrases = []
        for strategy, description in strategies:
            try:
                paraphrase = self._apply_paraphrase_strategy(sentence, strategy)
                if paraphrase and paraphrase != sentence:
                    paraphrases.append({
                        'text': paraphrase,
                        'strategy': strategy,
                        'description': description,
                        'translation_score': self._score_translation_readiness(paraphrase)
                    })
            except Exception as e:
                print(f"⚠️ Paraphrase failed for {strategy}: {e}")
        
        return paraphrases
    
    def _apply_paraphrase_strategy(self, sentence: str, strategy: str) -> str:
        """Apply paraphrasing strategy using Ollama"""
        prompts = {
            'formal_medical': f'Rewrite in formal medical style: "{sentence}"',
            'simplified_clarity': f'Rewrite for clarity: "{sentence}"',
            'action_oriented': f'Rewrite emphasizing actions: "{sentence}"'
        }
        
        try:
            response = requests.post(self.ollama_url, json={
                "model": self.model,
                "prompt": prompts[strategy],
                "stream": False,
                "options": {"temperature": 0.3, "max_tokens": 150}
            }, timeout=20)
            
            if response.status_code == 200:
                result = response.json()
                paraphrase = result.get('response', '').strip()
                paraphrase = re.sub(r'^(Rewritten|Response):', '', paraphrase).strip().strip('"\'')
                return paraphrase if paraphrase else sentence
        except:
            pass
        
        return sentence
    
    # Scoring methods (simplified for space)
    def _check_health_domain(self, sentence: str) -> float:
        found = [kw for kw in self.health_keywords if kw in sentence.lower()]
        return min(1.0, len(found) * 0.2)
    
    def _assess_completeness(self, sentence: str) -> float:
        has_subject = bool(re.search(r'\b(the|a|an|this|that)\b', sentence.lower()))
        has_verb = bool(re.search(r'\b(is|are|was|were|has|have|will|can|should|must)\b', sentence.lower()))
        ends_properly = sentence.strip().endswith(('.', '!', '?'))
        
        score = 0
        if has_subject: score += 0.4
        if has_verb: score += 0.4
        if ends_properly: score += 0.2
        return score
    
    def _check_logical_flow(self, sentence: str) -> float:
        word_count = len(sentence.split())
        if 5 <= word_count <= 25:
            return 0.9
        elif word_count < 5:
            return 0.3
        else:
            return 0.6
    
    def _check_grammar(self, sentence: str) -> float:
        issues = 0
        if not sentence[0].isupper(): issues += 1
        if not sentence.strip().endswith(('.', '!', '?')): issues += 1
        if '  ' in sentence: issues += 1
        return max(0.0, 1.0 - (issues * 0.2))
    
    def _assess_clarity(self, sentence: str) -> float:
        word_count = len(sentence.split())
        if 8 <= word_count <= 20:
            return 1.0
        elif 5 <= word_count <= 30:
            return 0.8
        else:
            return 0.5
    
    def _calculate_readability(self, sentence: str) -> float:
        words = sentence.split()
        if not words:
            return 0.0
        
        syllables = sum(max(1, len(re.findall(r'[aeiouAEIOU]', word))) for word in words)
        avg_syllables = syllables / len(words)
        
        if avg_syllables <= 1.5: return 1.0
        elif avg_syllables <= 2.0: return 0.8
        else: return 0.6
    
    def _calculate_information_density(self, sentence: str) -> float:
        words = sentence.split()
        content_words = [w for w in words if len(w) > 3]
        return len(content_words) / len(words) if words else 0.0
    
    def _assess_actionability(self, sentence: str) -> float:
        action_words = ['should', 'must', 'need', 'require', 'implement', 'monitor']
        count = sum(1 for word in action_words if word in sentence.lower())
        return min(1.0, count * 0.3)
    
    def _assess_cultural_transferability(self, sentence: str) -> float:
        barriers = ['american', 'european', 'western', 'local', 'traditional']
        barrier_count = sum(1 for b in barriers if b in sentence.lower())
        return max(0.3, 1.0 - barrier_count * 0.2)
    
    def _assess_terminology_usage(self, sentence: str) -> float:
        medical_terms = [kw for kw in self.health_keywords if kw in sentence.lower()]
        return min(1.0, len(medical_terms) * 0.25)
    
    def _assess_ambiguity(self, sentence: str) -> float:
        ambiguous = ['it', 'this', 'that', 'they', 'some', 'many']
        count = sum(1 for word in ambiguous if f' {word} ' in f' {sentence.lower()} ')
        return min(1.0, count * 0.2)
    
    def _score_translation_readiness(self, sentence: str) -> float:
        clarity = self._assess_clarity(sentence)
        completeness = self._assess_completeness(sentence)
        cultural = self._assess_cultural_transferability(sentence)
        return (clarity + completeness + cultural) / 3
    
    def _calculate_weighted_score(self, reasoning_results: Dict) -> float:
        weights = {'context_analysis': 0.35, 'linguistic_quality': 0.25, 
                  'content_value': 0.20, 'translation_readiness': 0.20}
        
        total = sum(reasoning_results[cat]['overall_score'] * weight 
                   for cat, weight in weights.items() if cat in reasoning_results)
        return min(1.0, total)
    
    def _get_primary_rejection_reason(self, reasoning_results: Dict) -> str:
        lowest_score = min(results['overall_score'] for results in reasoning_results.values())
        return f"Low overall quality score: {lowest_score:.2f}"
    
    def _quick_filter(self, sentence: str) -> Tuple[bool, str]:
        sentence = sentence.strip()
        
        if len(sentence) < 10:
            return False, "Too short"
        if len(sentence) > 500:
            return False, "Too long"
        
        for pattern in self.noise_patterns:
            if re.match(pattern, sentence, re.IGNORECASE):
                return False, f"Noise pattern"
        
        if not re.search(r'[a-zA-Z]', sentence):
            return False, "No alphabetic content"
        
        if len(sentence.split()) < 3:
            return False, "Too few words"
        
        return True, "Passed"
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text using pdfplumber"""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"⚠️ PDF extraction failed: {e}")
        return text
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Clean text
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if (line and not re.match(r'^\d+$', line) and 
                not re.match(r'^[ivx]+$', line, re.IGNORECASE) and len(line) >= 5):
                cleaned_lines.append(line)
        
        cleaned_text = ' '.join(cleaned_lines)
        
        # Split into sentences
        sentences = re.split(r'\. +', cleaned_text)
        filtered_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:
                filtered_sentences.append(sentence)
        
        return filtered_sentences

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python advanced_reasoning_processor.py <pdf_path>")
        sys.exit(1)
    
    processor = AdvancedReasoningProcessor()
    
    # Ask for detail level
    print("Choose detail level:")
    print("1. Full details (show every AI decision)")
    print("2. Progress only (show progress bar)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    detail_level = "full" if choice == "1" else "progress"
    
    results = processor.process_pdf(sys.argv[1], detail_level)
    
    # Save results
    output_file = f"advanced_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_file}")
