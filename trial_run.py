"""
Trial run script: Processes the first 25 sentences of a PDF using the advanced reasoning processor.
Outputs detailed reasoning and paraphrased variants for validation.
"""

import sys
import os
from pathlib import Path

# Import the advanced reasoning processor with paraphrasing
from advanced_reasoning_processor import process_pdf_with_advanced_reasoning

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
    results = process_pdf_with_advanced_reasoning(pdf_path, max_sentences=25, verbose=True)

    if not results or not results.get("sentences"):
        print("No sentences processed or error occurred.")
        sys.exit(2)

    for idx, sentence_info in enumerate(results["sentences"], 1):
        print(f"[{idx}] {sentence_info['sentence']}")
        print(f"  Approved: {sentence_info.get('approved', False)} | Overall Score: {sentence_info.get('overall_score', 0):.2f}")
        print(f"  Reasoning: {sentence_info.get('reasoning', 'N/A')}")
        
        # Show dimensional scores
        dim_scores = sentence_info.get('dimensional_scores', {})
        if dim_scores:
            print(f"  Dimensional Scores: Context={dim_scores.get('context_relevance', 0):.2f}, "
                  f"Complete={dim_scores.get('completeness', 0):.2f}, "
                  f"Health={dim_scores.get('health_relevance', 0):.2f}, "
                  f"Translation={dim_scores.get('translation_readiness', 0):.2f}")
        
        # Show paraphrases
        paraphrases = sentence_info.get('paraphrases', {})
        if paraphrases:
            print(f"  Paraphrases:")
            for style, variant in paraphrases.items():
                print(f"    {style}: {variant}")
        print()
    print("\n=== END OF TRIAL RUN ===\n")

if __name__ == "__main__":
    main()
