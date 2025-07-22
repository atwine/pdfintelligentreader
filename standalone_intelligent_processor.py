#!/usr/bin/env python3
"""
Standalone Intelligent PDF Processor with Ollama Health Context Agent
No external dependencies except pdfplumber and requests
"""

import json
import re
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests


class HealthContextAgent:
    """Intelligent agent for health context validation using Ollama"""
    
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
        self.api_url = "http://localhost:11434/api/generate"
        
        # Health context patterns
        self.health_keywords = [
            'health', 'disease', 'illness', 'infection', 'syndrome', 'disorder',
            'patient', 'treatment', 'diagnosis', 'therapy', 'medication', 'clinical',
            'surveillance', 'outbreak', 'epidemic', 'prevention', 'symptom',
            'fever', 'cough', 'pain', 'medical', 'care', 'hospital', 'clinic'
        ]
        
        # Noise patterns to filter out
        self.noise_patterns = [
            r'^[ivx]+\s*$',  # Roman numerals
            r'^\d+\s*$',     # Numbers alone
            r'^[A-Z\s]+$',   # All caps headers
            r'^(LIST OF|TABLE OF|FIGURE|APPENDIX|CHAPTER)',
            r'^\s*[.]{3,}',  # Dot leaders
            r'^\s*[-_=]{3,}',  # Lines
        ]
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama API"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 200}
            }
            
            response = requests.post(self.api_url, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json().get('response', '').strip()
            return None
            
        except Exception as e:
            print(f"Ollama API error: {e}")
            return None
    
    def _quick_filter(self, sentence: str) -> bool:
        """Quick rule-based filtering"""
        sentence = sentence.strip()
        
        # Length check
        if len(sentence) < 10 or len(sentence) > 500:
            return False
        
        # Noise patterns
        for pattern in self.noise_patterns:
            if re.match(pattern, sentence, re.IGNORECASE):
                return False
        
        # Must have alphabetic content
        if not re.search(r'[a-zA-Z]', sentence):
            return False
        
        # Must have reasonable word count
        if len(sentence.split()) < 3:
            return False
        
        return True
    
    def _has_health_context(self, sentence: str) -> bool:
        """Check for health context"""
        sentence_lower = sentence.lower()
        return any(keyword in sentence_lower for keyword in self.health_keywords)
    
    def _rule_based_analysis(self, sentence: str) -> Dict[str, Any]:
        """Fallback rule-based analysis"""
        sentence_lower = sentence.lower()
        
        # Check for complete thought indicators
        has_verb = bool(re.search(r'\b(is|are|was|were|have|has|will|should|must|can|may|do|does|did)\b', sentence_lower))
        has_subject = bool(re.search(r'\b(the|a|an|this|that|these|those|patient|case|health|disease|surveillance)\b', sentence_lower))
        has_health = self._has_health_context(sentence)
        
        # Quality assessment
        word_count = len(sentence.split())
        is_reasonable_length = 5 <= word_count <= 50
        
        # Overall assessment
        is_meaningful = has_verb and has_subject and has_health and is_reasonable_length
        confidence = 0.8 if is_meaningful else 0.3
        
        return {
            'is_meaningful': is_meaningful,
            'has_health_context': has_health,
            'confidence': confidence,
            'reasoning': f"Rule-based: verb={has_verb}, subject={has_subject}, health={has_health}, length_ok={is_reasonable_length}",
            'action': 'keep' if is_meaningful else 'discard'
        }
    
    def _ai_analysis(self, sentence: str) -> Optional[Dict[str, Any]]:
        """AI-powered analysis using Ollama"""
        
        prompt = f"""Analyze this sentence from a health document. Is it a meaningful, complete sentence with health/medical content suitable for translation?

Sentence: "{sentence}"

Respond with JSON only:
{{
    "meaningful": true/false,
    "complete_thought": true/false,
    "health_content": true/false,
    "confidence": 0.0-1.0,
    "category": "content|header|fragment|noise",
    "action": "keep|discard"
}}"""
        
        response = self._call_ollama(prompt)
        if response:
            try:
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
        
        return None
    
    def analyze_sentence(self, sentence: str) -> Dict[str, Any]:
        """Analyze a sentence with AI + rule-based fallback"""
        
        # Quick filter first
        if not self._quick_filter(sentence):
            return {
                'sentence': sentence,
                'is_meaningful': False,
                'confidence': 0.9,
                'reasoning': 'Failed quick filter (too short, noise pattern, or non-alphabetic)',
                'action': 'discard',
                'method': 'quick_filter'
            }
        
        # Try AI analysis first
        ai_result = self._ai_analysis(sentence)
        if ai_result and ai_result.get('confidence', 0) > 0.6:
            return {
                'sentence': sentence,
                'is_meaningful': ai_result.get('meaningful', False),
                'has_health_context': ai_result.get('health_content', False),
                'confidence': ai_result.get('confidence', 0.5),
                'reasoning': f"AI analysis: {ai_result.get('category', 'unknown')}",
                'action': ai_result.get('action', 'discard'),
                'method': 'ai_ollama'
            }
        
        # Fallback to rule-based
        rule_result = self._rule_based_analysis(sentence)
        return {
            'sentence': sentence,
            'is_meaningful': rule_result['is_meaningful'],
            'has_health_context': rule_result['has_health_context'],
            'confidence': rule_result['confidence'],
            'reasoning': rule_result['reasoning'],
            'action': rule_result['action'],
            'method': 'rule_based'
        }
    
    def filter_sentences(self, sentences: List[str]) -> List[Dict[str, Any]]:
        """Filter sentences and return meaningful ones"""
        
        results = []
        kept_count = 0
        
        for i, sentence in enumerate(sentences):
            if i % 100 == 0:
                print(f"   Analyzing sentence {i+1}/{len(sentences)}...")
            
            analysis = self.analyze_sentence(sentence)
            
            if analysis['action'] == 'keep' and analysis['confidence'] >= 0.6:
                results.append({
                    'sentence': sentence,
                    'analysis': analysis,
                    'metadata': {
                        'length': len(sentence),
                        'word_count': len(sentence.split()),
                        'position': i + 1
                    }
                })
                kept_count += 1
        
        print(f"   Kept {kept_count}/{len(sentences)} sentences ({(kept_count/len(sentences)*100):.1f}%)")
        return results


def extract_text(pdf_path: str) -> Optional[str]:
    """Extract text from PDF"""
    try:
        import pdfplumber
        
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            print(f"   Extracting from {len(pdf.pages)} pages...")
            
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        return text
        
    except Exception as e:
        print(f"❌ Text extraction failed: {e}")
        return None


def preprocess_text(text: str) -> List[str]:
    """Preprocess text and extract sentences"""
    
    # Clean up text
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Remove obvious artifacts
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if (line and 
            not re.match(r'^\d+$', line) and  # Page numbers
            not re.match(r'^[ivx]+$', line, re.IGNORECASE) and  # Roman numerals
            len(line) >= 5):
            cleaned_lines.append(line)
    
    # Rejoin and split into sentences
    cleaned_text = ' '.join(cleaned_lines)
    
    # Enhanced sentence splitting
    # Split on sentence endings but be careful with abbreviations
    # Fixed regex pattern for proper sentence splitting
    sentences = re.split(r'\. +', cleaned_text)
    
    # Filter out abbreviations that got split incorrectly
    filtered_sentences = []
    abbreviations = ['Dr', 'Mr', 'Mrs', 'Ms', 'Prof', 'vs', 'etc', 'i.e', 'e.g']
    
    for sentence in sentences:
        sentence = sentence.strip()
        # Skip if it's just an abbreviation
        if sentence not in abbreviations and len(sentence) > 3:
            filtered_sentences.append(sentence)
    
    sentences = filtered_sentences
    
    # Also split on other endings
    final_sentences = []
    for sentence in sentences:
        parts = re.split(r'[!?]+\s+', sentence)
        for part in parts:
            part = part.strip()
            if part and len(part) >= 10:
                final_sentences.append(part)
    
    return final_sentences


def main():
    """Main processing function"""
    
    if len(sys.argv) < 2:
        print("Usage: python standalone_intelligent_processor.py <pdf_file>")
        return
    
    pdf_file = sys.argv[1]
    
    if not os.path.exists(pdf_file):
        print(f"❌ File not found: {pdf_file}")
        return
    
    print("🧠 INTELLIGENT PDF PROCESSING WITH HEALTH CONTEXT")
    print("=" * 60)
    print(f"📄 Input: {os.path.basename(pdf_file)}")
    
    # Step 1: Extract text
    print("\n🔧 Step 1: Extracting text...")
    text = extract_text(pdf_file)
    if not text:
        return
    
    print(f"✅ Extracted {len(text)} characters")
    
    # Step 2: Preprocess and extract sentences
    print("\n📝 Step 2: Preprocessing and sentence extraction...")
    sentences = preprocess_text(text)
    print(f"✅ Found {len(sentences)} potential sentences")
    
    # Step 3: Initialize intelligent agent
    print("\n🧠 Step 3: Initializing health context agent...")
    agent = HealthContextAgent()
    print("✅ Agent ready")
    
    # Step 4: Intelligent filtering
    print("\n🔍 Step 4: Intelligent analysis and filtering...")
    meaningful_sentences = agent.filter_sentences(sentences)
    
    # Step 5: Prepare results
    results = {
        'metadata': {
            'processed_at': datetime.now().isoformat(),
            'source_file': pdf_file,
            'total_raw_sentences': len(sentences),
            'meaningful_sentences': len(meaningful_sentences),
            'improvement_ratio': f"{((len(sentences) - len(meaningful_sentences)) / len(sentences) * 100):.1f}% noise filtered"
        },
        'sentences': meaningful_sentences
    }
    
    # Step 6: Save results
    output_file = f"output/{Path(pdf_file).stem}_intelligent.json"
    os.makedirs("output", exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 INTELLIGENT PROCESSING COMPLETE!")
    print(f"📊 Results:")
    print(f"   Original sentences: {len(sentences)}")
    print(f"   Meaningful sentences: {len(meaningful_sentences)}")
    print(f"   Quality improvement: {results['metadata']['improvement_ratio']}")
    print(f"   Output saved: {output_file}")
    
    # Show samples
    if meaningful_sentences:
        print(f"\n📋 Sample meaningful sentences:")
        for i, item in enumerate(meaningful_sentences[:5], 1):
            sentence = item['sentence']
            confidence = item['analysis']['confidence']
            print(f"{i}. [{confidence:.2f}] {sentence[:100]}...")


if __name__ == "__main__":
    main()
