#!/usr/bin/env python3
"""
Enhanced Intelligent PDF Processor with Progress Bar and Agent Interaction Logging
"""

import json
import re
import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests


class ProgressBar:
    """Simple progress bar for terminal"""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
    
    def update(self, increment: int = 1, status: str = ""):
        """Update progress bar"""
        self.current += increment
        if self.current > self.total:
            self.current = self.total
        
        # Calculate percentage and time
        percentage = (self.current / self.total) * 100
        elapsed = time.time() - self.start_time
        
        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = f"ETA: {int(eta//60)}m{int(eta%60)}s"
        else:
            eta_str = "ETA: --"
        
        # Create progress bar
        bar_length = 40
        filled_length = int(bar_length * self.current // self.total)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        # Print progress
        print(f"\r{self.description}: [{bar}] {percentage:.1f}% ({self.current}/{self.total}) {eta_str} {status}", end='', flush=True)
        
        if self.current == self.total:
            print()  # New line when complete


class EnhancedHealthAgent:
    """Enhanced intelligent agent with detailed logging"""
    
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
        self.api_url = "http://localhost:11434/api/generate"
        
        # Statistics tracking
        self.stats = {
            'total_analyzed': 0,
            'ai_decisions': 0,
            'rule_decisions': 0,
            'kept_sentences': 0,
            'discarded_sentences': 0,
            'health_relevant': 0,
            'processing_time': 0
        }
        
        # Health context patterns
        self.health_keywords = [
            'health', 'disease', 'illness', 'infection', 'syndrome', 'disorder',
            'patient', 'treatment', 'diagnosis', 'therapy', 'medication', 'clinical',
            'surveillance', 'outbreak', 'epidemic', 'prevention', 'symptom',
            'fever', 'cough', 'pain', 'medical', 'care', 'hospital', 'clinic',
            'WHO', 'CDC', 'ministry', 'public health', 'case', 'investigation'
        ]
        
        # Noise patterns
        self.noise_patterns = [
            r'^[ivx]+\s*$',  # Roman numerals
            r'^\d+\s*$',     # Numbers alone
            r'^[A-Z\s]+$',   # All caps headers
            r'^(LIST OF|TABLE OF|FIGURE|APPENDIX|CHAPTER)',
            r'^\s*[.]{3,}',  # Dot leaders
            r'^\s*[-_=]{3,}',  # Lines
        ]
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama API with detailed logging"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 150}
            }
            
            start_time = time.time()
            response = requests.post(self.api_url, json=payload, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json().get('response', '').strip()
                print(f"    🤖 AI Response ({response_time:.1f}s): {result[:100]}...")
                return result
            else:
                print(f"    ❌ AI Error: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"    ❌ AI Error: {e}")
            return None
    
    def _quick_filter(self, sentence: str) -> tuple[bool, str]:
        """Quick rule-based filtering with reasoning"""
        sentence = sentence.strip()
        
        # Length check
        if len(sentence) < 10:
            return False, "Too short (< 10 chars)"
        if len(sentence) > 500:
            return False, "Too long (> 500 chars)"
        
        # Noise patterns
        for pattern in self.noise_patterns:
            if re.match(pattern, sentence, re.IGNORECASE):
                return False, f"Noise pattern: {pattern}"
        
        # Must have alphabetic content
        if not re.search(r'[a-zA-Z]', sentence):
            return False, "No alphabetic content"
        
        # Must have reasonable word count
        if len(sentence.split()) < 3:
            return False, "Too few words (< 3)"
        
        return True, "Passed quick filter"
    
    def _has_health_context(self, sentence: str) -> tuple[bool, float, str]:
        """Check for health context with detailed reasoning"""
        sentence_lower = sentence.lower()
        found_keywords = []
        
        for keyword in self.health_keywords:
            if keyword in sentence_lower:
                found_keywords.append(keyword)
        
        health_score = min(1.0, len(found_keywords) * 0.2)
        has_health = health_score > 0.3
        
        reasoning = f"Health keywords found: {found_keywords[:3]}" if found_keywords else "No health keywords"
        
        return has_health, health_score, reasoning
    
    def _ai_analysis(self, sentence: str) -> Optional[Dict[str, Any]]:
        """AI-powered analysis with detailed interaction"""
        
        print(f"    🧠 Asking AI about: '{sentence[:60]}...'")
        
        prompt = f"""You are analyzing a sentence from a health surveillance document. 

Sentence: "{sentence}"

Analyze if this is meaningful health content suitable for translation:
1. Is it a complete sentence with health/medical information?
2. Does it contain actionable or informative content?
3. Is it NOT just navigation (headers, page numbers, table of contents)?

Respond with: KEEP or DISCARD, then explain why in 1-2 sentences."""
        
        response = self._call_ollama(prompt)
        if response:
            try:
                decision = "KEEP" if "KEEP" in response.upper() else "DISCARD"
                reasoning = response.replace("KEEP", "").replace("DISCARD", "").strip()
                
                confidence = 0.9 if "KEEP" in response.upper() else 0.1
                
                return {
                    'decision': decision,
                    'reasoning': reasoning,
                    'confidence': confidence,
                    'method': 'ai_ollama'
                }
            except:
                pass
        
        return None
    
    def _rule_based_analysis(self, sentence: str) -> Dict[str, Any]:
        """Fallback rule-based analysis with reasoning"""
        sentence_lower = sentence.lower()
        
        # Check for complete thought indicators
        has_verb = bool(re.search(r'\b(is|are|was|were|have|has|will|should|must|can|may|do|does|did)\b', sentence_lower))
        has_subject = bool(re.search(r'\b(the|a|an|this|that|these|those|patient|case|health|disease|surveillance)\b', sentence_lower))
        has_health, health_score, health_reason = self._has_health_context(sentence)
        
        # Quality assessment
        word_count = len(sentence.split())
        is_reasonable_length = 5 <= word_count <= 50
        
        # Overall assessment
        is_meaningful = has_verb and has_subject and has_health and is_reasonable_length
        confidence = 0.8 if is_meaningful else 0.3
        
        reasoning = f"Rule-based: verb={has_verb}, subject={has_subject}, health={has_health}, length_ok={is_reasonable_length}. {health_reason}"
        
        return {
            'decision': 'KEEP' if is_meaningful else 'DISCARD',
            'reasoning': reasoning,
            'confidence': confidence,
            'method': 'rule_based'
        }
    
    def analyze_sentence(self, sentence: str, show_details: bool = True) -> Dict[str, Any]:
        """Analyze a sentence with detailed agent interaction"""
        
        self.stats['total_analyzed'] += 1
        start_time = time.time()
        
        if show_details:
            print(f"\n📝 Analyzing sentence #{self.stats['total_analyzed']}")
            print(f"    Text: '{sentence[:80]}...'")
        
        # Quick filter first
        passes_filter, filter_reason = self._quick_filter(sentence)
        if not passes_filter:
            self.stats['discarded_sentences'] += 1
            self.stats['rule_decisions'] += 1
            
            if show_details:
                print(f"    ⚡ Quick Filter: ❌ DISCARD - {filter_reason}")
            
            return {
                'sentence': sentence,
                'decision': 'DISCARD',
                'reasoning': f"Quick filter: {filter_reason}",
                'confidence': 0.95,
                'method': 'quick_filter'
            }
        
        if show_details:
            print(f"    ⚡ Quick Filter: ✅ PASS - {filter_reason}")
        
        # Try AI analysis first
        ai_result = self._ai_analysis(sentence)
        if ai_result and ai_result.get('confidence', 0) > 0.6:
            self.stats['ai_decisions'] += 1
            
            if ai_result['decision'] == 'KEEP':
                self.stats['kept_sentences'] += 1
                # Check if health relevant
                has_health, _, _ = self._has_health_context(sentence)
                if has_health:
                    self.stats['health_relevant'] += 1
            else:
                self.stats['discarded_sentences'] += 1
            
            if show_details:
                decision_icon = "✅" if ai_result['decision'] == 'KEEP' else "❌"
                print(f"    🤖 AI Decision: {decision_icon} {ai_result['decision']} - {ai_result['reasoning']}")
            
            result = {
                'sentence': sentence,
                'decision': ai_result['decision'],
                'reasoning': ai_result['reasoning'],
                'confidence': ai_result['confidence'],
                'method': 'ai_ollama'
            }
        else:
            # Fallback to rule-based
            rule_result = self._rule_based_analysis(sentence)
            self.stats['rule_decisions'] += 1
            
            if rule_result['decision'] == 'KEEP':
                self.stats['kept_sentences'] += 1
                has_health, _, _ = self._has_health_context(sentence)
                if has_health:
                    self.stats['health_relevant'] += 1
            else:
                self.stats['discarded_sentences'] += 1
            
            if show_details:
                decision_icon = "✅" if rule_result['decision'] == 'KEEP' else "❌"
                print(f"    📋 Rule Decision: {decision_icon} {rule_result['decision']} - {rule_result['reasoning']}")
            
            result = rule_result
            result['sentence'] = sentence
        
        # Update timing
        processing_time = time.time() - start_time
        self.stats['processing_time'] += processing_time
        
        if show_details:
            print(f"    ⏱️ Processing time: {processing_time:.2f}s")
        
        return result
    
    def get_stats_summary(self) -> str:
        """Get processing statistics summary"""
        if self.stats['total_analyzed'] == 0:
            return "No sentences analyzed yet"
        
        ai_percentage = (self.stats['ai_decisions'] / self.stats['total_analyzed']) * 100
        keep_rate = (self.stats['kept_sentences'] / self.stats['total_analyzed']) * 100
        health_rate = (self.stats['health_relevant'] / max(1, self.stats['kept_sentences'])) * 100
        avg_time = self.stats['processing_time'] / self.stats['total_analyzed']
        
        return f"""
📊 PROCESSING STATISTICS:
   Total analyzed: {self.stats['total_analyzed']}
   AI decisions: {self.stats['ai_decisions']} ({ai_percentage:.1f}%)
   Rule decisions: {self.stats['rule_decisions']} ({100-ai_percentage:.1f}%)
   Kept sentences: {self.stats['kept_sentences']} ({keep_rate:.1f}%)
   Health relevant: {self.stats['health_relevant']} ({health_rate:.1f}% of kept)
   Avg processing time: {avg_time:.2f}s per sentence
   Total processing time: {self.stats['processing_time']:.1f}s
"""


def extract_text(pdf_path: str) -> Optional[str]:
    """Extract text from PDF with progress"""
    try:
        import pdfplumber
        
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            progress = ProgressBar(total_pages, "📄 Extracting text")
            
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                
                progress.update(1, f"Page {i+1}")
                
                # Show sample every 50 pages
                if i % 50 == 0 and page_text:
                    sample = page_text[:100].replace('\n', ' ')
                    print(f"\n    Sample from page {i+1}: '{sample}...'")
        
        return text
        
    except Exception as e:
        print(f"❌ Text extraction failed: {e}")
        return None


def preprocess_text(text: str) -> List[str]:
    """Preprocess text and extract sentences with progress"""
    
    print("\n🔧 PREPROCESSING TEXT")
    print("=" * 40)
    
    # Clean up text
    print("   Normalizing whitespace...")
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Remove obvious artifacts
    print("   Removing artifacts...")
    lines = text.split('\n')
    cleaned_lines = []
    
    artifacts_removed = 0
    for line in lines:
        line = line.strip()
        if (line and 
            not re.match(r'^\d+$', line) and  # Page numbers
            not re.match(r'^[ivx]+$', line, re.IGNORECASE) and  # Roman numerals
            len(line) >= 5):
            cleaned_lines.append(line)
        else:
            artifacts_removed += 1
    
    print(f"   Removed {artifacts_removed} artifacts")
    
    # Rejoin and split into sentences
    print("   Splitting into sentences...")
    cleaned_text = ' '.join(cleaned_lines)
    
    # Simple sentence splitting
    sentences = re.split(r'\. +', cleaned_text)
    
    # Filter out abbreviations and clean up
    final_sentences = []
    abbreviations = ['Dr', 'Mr', 'Mrs', 'Ms', 'Prof', 'vs', 'etc', 'i.e', 'e.g']
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence not in abbreviations and len(sentence) >= 10:
            final_sentences.append(sentence)
    
    print(f"   Found {len(final_sentences)} potential sentences")
    return final_sentences


def main():
    """Main processing function with enhanced interaction"""
    
    if len(sys.argv) < 2:
        print("Usage: python enhanced_intelligent_processor.py <pdf_file>")
        return
    
    pdf_file = sys.argv[1]
    
    if not os.path.exists(pdf_file):
        print(f"❌ File not found: {pdf_file}")
        return
    
    print("🧠 ENHANCED INTELLIGENT PDF PROCESSING")
    print("=" * 60)
    print(f"📄 Input: {os.path.basename(pdf_file)}")
    print(f"🕒 Started: {datetime.now().strftime('%H:%M:%S')}")
    
    # Step 1: Extract text
    print(f"\n🔧 STEP 1: TEXT EXTRACTION")
    print("=" * 40)
    text = extract_text(pdf_file)
    if not text:
        return
    
    print(f"\n✅ Extracted {len(text):,} characters")
    
    # Step 2: Preprocess and extract sentences
    sentences = preprocess_text(text)
    
    # Step 3: Initialize intelligent agent
    print(f"\n🧠 STEP 3: INITIALIZING INTELLIGENT AGENT")
    print("=" * 40)
    agent = EnhancedHealthAgent()
    print("✅ Agent ready with health context intelligence")
    
    # Step 4: Intelligent analysis with progress and interaction
    print(f"\n🔍 STEP 4: INTELLIGENT ANALYSIS")
    print("=" * 40)
    print(f"Analyzing {len(sentences)} sentences with AI reasoning...")
    
    # Ask user about detail level
    print(f"\nChoose detail level:")
    print(f"1. Full details (show every AI decision)")
    print(f"2. Progress only (show progress bar)")
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
        show_details = choice == "1"
    except:
        show_details = False
    
    meaningful_sentences = []
    progress = ProgressBar(len(sentences), "🤖 AI Analysis")
    
    for i, sentence in enumerate(sentences):
        analysis = agent.analyze_sentence(sentence, show_details=show_details)
        
        if analysis['decision'] == 'KEEP' and analysis['confidence'] >= 0.6:
            meaningful_sentences.append({
                'sentence': sentence,
                'analysis': analysis,
                'metadata': {
                    'length': len(sentence),
                    'word_count': len(sentence.split()),
                    'position': i + 1
                }
            })
        
        if not show_details:
            status = f"Kept: {len(meaningful_sentences)}"
            progress.update(1, status)
        
        # Show periodic stats
        if (i + 1) % 100 == 0:
            print(agent.get_stats_summary())
    
    # Final results
    print(f"\n" + "=" * 60)
    print("🎉 PROCESSING COMPLETE!")
    print(agent.get_stats_summary())
    
    # Save results
    output_file = f"output/{os.path.splitext(os.path.basename(pdf_file))[0]}_enhanced_intelligent.json"
    os.makedirs("output", exist_ok=True)
    
    results = {
        'metadata': {
            'processed_at': datetime.now().isoformat(),
            'source_file': pdf_file,
            'total_raw_sentences': len(sentences),
            'meaningful_sentences': len(meaningful_sentences),
            'processing_stats': agent.stats,
            'improvement_ratio': f"{((len(sentences) - len(meaningful_sentences)) / len(sentences) * 100):.1f}% noise filtered"
        },
        'sentences': meaningful_sentences
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Show sample results
    if meaningful_sentences:
        print(f"\n📋 SAMPLE MEANINGFUL SENTENCES:")
        for i, item in enumerate(meaningful_sentences[:5], 1):
            sentence = item['sentence']
            confidence = item['analysis']['confidence']
            method = item['analysis']['method']
            print(f"{i}. [{confidence:.2f}|{method}] {sentence[:100]}...")


if __name__ == "__main__":
    main()
