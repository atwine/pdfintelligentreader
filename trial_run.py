"""
Trial run script: Processes the first 25 sentences of a PDF using the advanced reasoning processor.
Outputs detailed reasoning and paraphrased variants for validation.
"""

import sys
import os
from pathlib import Path

# Import the minimal trial runner from enhanced_intelligent_processor
from enhanced_intelligent_processor import process_pdf_trial

def main():
    if len(sys.argv) < 2:
        print("Usage: python trial_run.py <PDF_PATH>")
        sys.exit(1)
    pdf_path = sys.argv[1]
    if not Path(pdf_path).exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    print("\n=== TRIAL RUN: ADVANCED REASONING (First 25 Sentences) ===\n")
    # Process the PDF, limiting to 25 sentences for quick validation
    results = process_pdf_trial(pdf_path, max_sentences=25, verbose=True)

    if not results or not results.get("sentences"):
        print("No sentences processed or error occurred.")
        sys.exit(2)

    for idx, sentence_info in enumerate(results["sentences"], 1):
        print(f"[{idx}] {sentence_info['text']}")
        print(f"  Approved: {sentence_info.get('approved', False)} | Score: {sentence_info.get('score', 0):.2f}")
        print(f"  Reasoning: {sentence_info.get('reasoning', 'N/A')}")
        paraphrases = sentence_info.get('paraphrases')
        if paraphrases:
            for style, variant in paraphrases.items():
                print(f"    Paraphrase ({style}): {variant}")
        print()
    print("\n=== END OF TRIAL RUN ===\n")

if __name__ == "__main__":
    main()
