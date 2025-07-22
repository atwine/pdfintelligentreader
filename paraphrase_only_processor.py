#!/usr/bin/env python3
"""
Streamlined Paraphrase-Only Processor
Outputs only approved sentences with their paraphrases - clean, minimal output
"""

import json
import re
import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests


class StreamlinedParaphraseProcessor:
    """Minimal processor focused on clean paraphrase output"""
    
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
        self.api_url = "http://localhost:11434/api/generate"
        
        # Health context vocabulary (comprehensive)
        self.health_keywords = [
            'health', 'disease', 'illness', 'infection', 'syndrome', 'disorder',
            'patient', 'treatment', 'diagnosis', 'therapy', 'medication', 'clinical',
            'surveillance', 'outbreak', 'epidemic', 'pandemic', 'prevention', 'symptom',
            'fever', 'cough', 'pain', 'medical', 'care', 'hospital', 'clinic',
            'WHO', 'CDC', 'ministry', 'public health', 'case', 'investigation',
            'community', 'facility', 'reporting', 'notification', 'response',
            'laboratory', 'specimen', 'testing', 'vaccine', 'immunization',
            'mortality', 'morbidity', 'incidence', 'prevalence', 'transmission',
            'guidelines', 'protocol', 'policy', 'national', 'public', 'workers',
            'system', 'data', 'information', 'monitoring', 'assessment', 'control'
        ]
        
        self.stats = {'processed': 0, 'approved': 0, 'paraphrases': 0}
    
    def is_sentence_approved(self, sentence: str) -> bool:
        """Determine if sentence should be approved for paraphrasing"""
        sentence = sentence.strip()
        
        # Basic quality checks
        if len(sentence) < 20 or len(sentence) > 400:
            return False
        if len(sentence.split()) < 5:
            return False
        
        # Avoid navigation/headers/artifacts
        if re.match(r'^\s*[ivx\d]+\s*[.\s]*[A-Z\s]+\s*[.]+\s*$', sentence, re.IGNORECASE):
            return False
        if sentence.isupper() and len(sentence.split()) <= 8:
            return False
        if re.match(r'^\s*[A-Z\s]+\s*$', sentence) and len(sentence.split()) <= 6:
            return False
        
        # Must have proper sentence structure
        if not sentence[0].isupper():
            return False
        if not sentence.endswith(('.', '!', '?', ':')):
            return False
        
        # Health relevance check (balanced - need health context)
        sentence_lower = sentence.lower()
        health_keywords_found = [kw for kw in self.health_keywords if kw in sentence_lower]
        
        strong_keywords = ['surveillance', 'outbreak', 'epidemic', 'disease', 'health', 'medical', 'clinical']
        strong_matches = [kw for kw in strong_keywords if kw in sentence_lower]
        
        # More reasonable: 1+ health keywords OR 1 strong keyword
        health_approved = len(health_keywords_found) >= 1 or len(strong_matches) >= 1
        
        # Must have basic sentence structure (expanded patterns)
        has_verb = bool(re.search(r'\b(is|are|was|were|have|has|will|should|must|can|may|do|does|did|include|provide|ensure|establish|implement|contain|involve|require|play|adapt|incorporate|reflect|support|enable|facilitate|promote|develop|maintain|improve|enhance|strengthen|conduct|perform|carry|take|make|give|offer|deliver|manage|coordinate|monitor|evaluate|assess|review|update|revise|modify|change|increase|decrease|reduce|prevent|control|treat|diagnose|identify|detect|report|notify|respond|investigate|analyze|collect|gather|compile|process|interpret|disseminate|communicate|train|educate|guide|direct|supervise|oversee)\b', sentence_lower))
        has_subject = bool(re.search(r'\b(the|a|an|this|that|these|those|patient|case|health|disease|surveillance|community|facility|system|process|guideline|protocol|worker|staff|team|person|individual|population|group|organization|institution|ministry|department|unit|program|project|initiative|strategy|approach|method|procedure|activity|action|measure|intervention|response|investigation|study|research|analysis|assessment|evaluation|review|monitoring|reporting|notification|data|information|evidence|finding|result|outcome|impact|effect|benefit|risk|threat|challenge|issue|problem|concern|priority|objective|goal|target|indicator|standard|criteria|requirement|recommendation|guidance|instruction|training|education|capacity|resource|tool|equipment|material|document|report|form|record|register|database|system)\b', sentence_lower))
        
        # Final approval decision
        return health_approved and has_verb and has_subject
    
    def generate_paraphrases(self, sentence: str) -> Dict[str, str]:
        """Generate validated paraphrases for approved sentences only"""
        
        strategies = {
            'formal': 'formal medical terminology and professional tone',
            'simple': 'simplified, clear language accessible to general audience', 
            'action': 'action-oriented, practical implementation focus'
        }
        
        paraphrases = {}
        
        for style, description in strategies.items():
            try:
                prompt = f"""Paraphrase this sentence using {description}:

"{sentence}"

Return only the paraphrased sentence, no explanations or additional text:"""
                
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2, "num_predict": 80}
                }
                
                response = requests.post(self.api_url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    result = response.json().get('response', '').strip()
                    
                    # Clean and validate the response
                    result = re.sub(r'^(Paraphrased version:|Paraphrase:)\s*', '', result, flags=re.IGNORECASE)
                    result = result.strip('"\'')
                    result = result.split('\n')[0].strip()  # Take only first line
                    
                    # Validation: must be different, reasonable length, proper structure
                    if (len(result) >= 15 and 
                        result != sentence and 
                        result[0].isupper() and 
                        result.endswith(('.', '!', '?', ':'))):
                        paraphrases[style] = result
                        
            except Exception:
                continue
        
        return paraphrases
    
    def process_pdf_clean(self, pdf_path: str, max_sentences: int = None) -> None:
        """Process PDF with clean, minimal output"""
        
        print(f"Processing: {os.path.basename(pdf_path)}")
        print("=" * 60)
        
        # Import text processing
        try:
            from enhanced_intelligent_processor import extract_text, preprocess_text
        except ImportError:
            print("Error: Could not import text processing functions")
            return
        
        # Extract and preprocess
        text = extract_text(pdf_path)
        if not text:
            print("Error: No text extracted")
            return
        
        sentences = preprocess_text(text)
        if max_sentences:
            sentences = sentences[:max_sentences]
        
        print(f"Analyzing {len(sentences)} sentences...\n")
        
        approved_count = 0
        
        for i, sentence in enumerate(sentences, 1):
            self.stats['processed'] += 1
            
            # Step 1: Approval decision (independent of paraphrase generation)
            if self.is_sentence_approved(sentence):
                approved_count += 1
                self.stats['approved'] += 1
                
                # Step 2: Generate paraphrases for approved sentence
                paraphrases = self.generate_paraphrases(sentence)
                
                # Step 3: Count successful paraphrases
                if paraphrases:
                    self.stats['paraphrases'] += len(paraphrases)
                
                # Step 4: Output (always show approved sentences, even if no paraphrases)
                print(f"[{approved_count}] ORIGINAL:")
                print(f"    {sentence}")
                
                if paraphrases:
                    print(f"    PARAPHRASES:")
                    for style, paraphrase in paraphrases.items():
                        print(f"    {style.upper()}: {paraphrase}")
                else:
                    print(f"    (No paraphrases generated)")
                print()
            
            # Progress indicator
            if i % 50 == 0:
                print(f"Progress: {i}/{len(sentences)} processed, {approved_count} approved")
        
        print("=" * 60)
        print(f"SUMMARY:")
        print(f"  Total processed: {self.stats['processed']}")
        print(f"  Approved: {self.stats['approved']}")
        print(f"  Paraphrases generated: {self.stats['paraphrases']}")
        print(f"  Approval rate: {(self.stats['approved']/self.stats['processed']*100):.1f}%")


def main():
    if len(sys.argv) < 2:
        print("Usage: python paraphrase_only_processor.py <pdf_file> [max_sentences]")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    max_sentences = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if not os.path.exists(pdf_file):
        print(f"Error: File not found: {pdf_file}")
        sys.exit(1)
    
    processor = StreamlinedParaphraseProcessor()
    processor.process_pdf_clean(pdf_file, max_sentences)


if __name__ == "__main__":
    main()
