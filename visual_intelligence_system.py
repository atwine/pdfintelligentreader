#!/usr/bin/env python3
"""
Advanced Visual Intelligence System for PDF Processing
Multi-agent system for extracting meaningful content from images, charts, and diagrams
"""

import json
import base64
import requests
import cv2
import numpy as np
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import io

class VisualIntelligenceSystem:
    """Advanced visual content processing with multi-agent architecture"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434/api/generate"):
        self.ollama_url = ollama_url
        self.vision_model = "llava:7b"   # Ollama vision model
        self.text_model = "llama3.1:8b"
        
        # Visual content types
        self.visual_types = {
            'flowchart': 'Process flow diagrams and decision trees',
            'organizational_chart': 'Hierarchy and reporting structures', 
            'process_diagram': 'Step-by-step procedures and workflows',
            'medical_diagram': 'Anatomical illustrations and medical processes',
            'data_visualization': 'Graphs, charts, and statistical representations',
            'table': 'Structured data in tabular format',
            'infographic': 'Information graphics and visual summaries',
            'screenshot': 'Interface screenshots and system displays'
        }
        
        # Health-specific visual patterns
        self.health_visual_keywords = [
            'surveillance', 'outbreak', 'epidemic', 'disease', 'patient flow',
            'reporting structure', 'health facility', 'data collection',
            'case management', 'laboratory', 'diagnosis', 'treatment pathway'
        ]
    
    def process_pdf_visuals(self, pdf_path: str) -> Dict:
        """Process all visual elements in PDF"""
        
        print(f"🔍 VISUAL INTELLIGENCE SYSTEM")
        print(f"📄 Processing: {pdf_path}")
        print("=" * 50)
        
        results = {
            'metadata': {
                'processed_at': datetime.now().isoformat(),
                'pdf_path': pdf_path,
                'vision_model': self.vision_model
            },
            'visual_elements': [],
            'generated_sentences': [],
            'processing_stats': {}
        }
        
        # Step 1: Extract visual elements
        print("🖼️ Step 1: Detecting visual elements...")
        visual_elements = self._extract_visual_elements(pdf_path)
        results['visual_elements'] = visual_elements
        
        print(f"   Found {len(visual_elements)} visual elements")
        
        # Step 2: Process each visual element
        print(f"\n🧠 Step 2: Processing visual content...")
        
        for i, element in enumerate(visual_elements, 1):
            print(f"\n📊 [{i}/{len(visual_elements)}] Processing {element['type']}...")
            
            # Multi-agent processing pipeline
            processed_element = self._process_visual_element(element)
            
            if processed_element['generated_sentences']:
                results['generated_sentences'].extend(processed_element['generated_sentences'])
                print(f"   ✅ Generated {len(processed_element['generated_sentences'])} sentences")
            else:
                print(f"   ⚠️ No sentences generated")
        
        # Step 3: Quality validation
        print(f"\n✅ Step 3: Quality validation...")
        validated_sentences = self._validate_generated_content(results['generated_sentences'])
        results['validated_sentences'] = validated_sentences
        
        # Statistics
        results['processing_stats'] = {
            'total_visual_elements': len(visual_elements),
            'sentences_generated': len(results['generated_sentences']),
            'sentences_validated': len(validated_sentences),
            'validation_rate': len(validated_sentences) / len(results['generated_sentences']) if results['generated_sentences'] else 0
        }
        
        print(f"\n🎉 VISUAL PROCESSING COMPLETE!")
        print(f"   📊 Elements: {len(visual_elements)}")
        print(f"   📝 Generated: {len(results['generated_sentences'])} sentences")
        print(f"   ✅ Validated: {len(validated_sentences)} sentences")
        
        return results
    
    def _extract_visual_elements(self, pdf_path: str) -> List[Dict]:
        """Extract visual elements from PDF"""
        visual_elements = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                
                # Get images
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        # Extract image
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            img_data = pix.tobytes("png")
                            
                            # Convert to PIL Image
                            pil_image = Image.open(io.BytesIO(img_data))
                            
                            # Classify visual type
                            visual_type = self._classify_visual_type(pil_image)
                            
                            element = {
                                'page': page_num + 1,
                                'index': img_index,
                                'type': visual_type,
                                'image_data': img_data,
                                'size': pil_image.size,
                                'bbox': page.get_image_bbox(img)
                            }
                            
                            visual_elements.append(element)
                        
                        pix = None
                        
                    except Exception as e:
                        print(f"   ⚠️ Error extracting image {img_index}: {e}")
                        continue
            
            doc.close()
            
        except Exception as e:
            print(f"❌ Error processing PDF: {e}")
        
        return visual_elements
    
    def _classify_visual_type(self, image: Image.Image) -> str:
        """Classify the type of visual content"""
        
        # Convert to OpenCV format for analysis
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            img_gray = img_array
        
        # Basic classification heuristics
        height, width = img_gray.shape
        aspect_ratio = width / height
        
        # Detect lines and shapes
        edges = cv2.Canny(img_gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=30, maxLineGap=10)
        
        # Count text regions using OCR
        try:
            text_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            text_regions = len([conf for conf in text_data['conf'] if int(conf) > 30])
        except:
            text_regions = 0
        
        # Classification logic
        if lines is not None and len(lines) > 10:
            if aspect_ratio > 1.5:
                return 'flowchart'
            elif text_regions > 5:
                return 'organizational_chart'
            else:
                return 'process_diagram'
        elif text_regions > 20:
            return 'table'
        elif aspect_ratio < 0.8:
            return 'medical_diagram'
        else:
            return 'infographic'
    
    def _process_visual_element(self, element: Dict) -> Dict:
        """Process individual visual element through multi-agent pipeline"""
        
        result = {
            'element': element,
            'ocr_text': '',
            'visual_analysis': {},
            'generated_sentences': [],
            'processing_method': []
        }
        
        # Agent 1: OCR Extraction
        result['ocr_text'] = self._extract_text_from_image(element['image_data'])
        if result['ocr_text']:
            result['processing_method'].append('ocr_extraction')
        
        # Agent 2: Visual Analysis
        result['visual_analysis'] = self._analyze_visual_content(element)
        result['processing_method'].append('visual_analysis')
        
        # Agent 3: Content Synthesis
        sentences = self._synthesize_content(element, result['ocr_text'], result['visual_analysis'])
        result['generated_sentences'] = sentences
        if sentences:
            result['processing_method'].append('content_synthesis')
        
        return result
    
    def _extract_text_from_image(self, image_data: bytes) -> str:
        """Extract text using OCR"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Use Tesseract OCR
            text = pytesseract.image_to_string(image, lang='eng')
            
            # Clean extracted text
            text = ' '.join(text.split())  # Remove extra whitespace
            text = text.strip()
            
            return text if len(text) > 5 else ''
            
        except Exception as e:
            print(f"   ⚠️ OCR extraction failed: {e}")
            return ''
    
    def _analyze_visual_content(self, element: Dict) -> Dict:
        """Analyze visual content using vision model"""
        
        analysis = {
            'content_type': element['type'],
            'complexity': 'medium',
            'key_elements': [],
            'relationships': [],
            'health_relevance': 0.0
        }
        
        try:
            # Convert image to base64 for vision model
            image_b64 = base64.b64encode(element['image_data']).decode('utf-8')
            
            # Analyze with vision model
            prompt = f"""
Analyze this {element['type']} image and describe:
1. Main visual elements and components
2. Relationships or flow between elements  
3. Key information being communicated
4. Relevance to health/medical context (0-1 score)

Focus on extracting meaningful information that can be converted to descriptive sentences.
"""
            
            response = requests.post(self.ollama_url.replace('/generate', '/api/generate'), json={
                "model": self.vision_model,
                "prompt": prompt,
                "images": [image_b64],
                "stream": False,
                "options": {"temperature": 0.3}
            }, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result.get('response', '')
                
                # Parse analysis (simplified)
                if 'health' in analysis_text.lower() or any(kw in analysis_text.lower() for kw in self.health_visual_keywords):
                    analysis['health_relevance'] = 0.8
                
                analysis['description'] = analysis_text
            
        except Exception as e:
            print(f"   ⚠️ Visual analysis failed: {e}")
            analysis['description'] = f"Unable to analyze {element['type']} content"
        
        return analysis
    
    def _synthesize_content(self, element: Dict, ocr_text: str, visual_analysis: Dict) -> List[Dict]:
        """Generate meaningful sentences from visual content"""
        
        sentences = []
        
        # Combine OCR text and visual analysis
        context = f"""
Visual Element: {element['type']}
OCR Text: {ocr_text}
Visual Analysis: {visual_analysis.get('description', '')}
Health Relevance: {visual_analysis.get('health_relevance', 0)}
"""
        
        # Generate sentences based on content type
        generation_strategies = {
            'flowchart': self._generate_flowchart_sentences,
            'organizational_chart': self._generate_org_chart_sentences,
            'process_diagram': self._generate_process_sentences,
            'medical_diagram': self._generate_medical_sentences,
            'table': self._generate_table_sentences,
            'infographic': self._generate_infographic_sentences
        }
        
        strategy = generation_strategies.get(element['type'], self._generate_generic_sentences)
        sentences = strategy(context, ocr_text, visual_analysis)
        
        return sentences
    
    def _generate_flowchart_sentences(self, context: str, ocr_text: str, analysis: Dict) -> List[Dict]:
        """Generate sentences for flowcharts"""
        
        prompt = f"""
Based on this flowchart information:
{context}

Generate 2-3 clear, descriptive sentences that explain:
1. What process or workflow is being shown
2. The main steps or decision points
3. The purpose or outcome of the process

Focus on health/medical context if relevant. Make sentences suitable for translation.

Sentences:"""
        
        return self._generate_with_ollama(prompt, 'flowchart_analysis')
    
    def _generate_org_chart_sentences(self, context: str, ocr_text: str, analysis: Dict) -> List[Dict]:
        """Generate sentences for organizational charts"""
        
        prompt = f"""
Based on this organizational chart:
{context}

Generate 2-3 sentences describing:
1. The organizational structure shown
2. Key roles and reporting relationships
3. The purpose of this organizational arrangement

Focus on health system context if applicable.

Sentences:"""
        
        return self._generate_with_ollama(prompt, 'organizational_analysis')
    
    def _generate_process_sentences(self, context: str, ocr_text: str, analysis: Dict) -> List[Dict]:
        """Generate sentences for process diagrams"""
        
        prompt = f"""
Based on this process diagram:
{context}

Generate 2-3 sentences explaining:
1. What process is being illustrated
2. The sequence of steps or stages
3. The intended outcome or purpose

Make it actionable and clear for health workers if relevant.

Sentences:"""
        
        return self._generate_with_ollama(prompt, 'process_analysis')
    
    def _generate_medical_sentences(self, context: str, ocr_text: str, analysis: Dict) -> List[Dict]:
        """Generate sentences for medical diagrams"""
        
        prompt = f"""
Based on this medical diagram:
{context}

Generate 2-3 educational sentences about:
1. What medical concept is illustrated
2. Key anatomical or physiological elements
3. Clinical or health significance

Use appropriate medical terminology suitable for health professionals.

Sentences:"""
        
        return self._generate_with_ollama(prompt, 'medical_analysis')
    
    def _generate_table_sentences(self, context: str, ocr_text: str, analysis: Dict) -> List[Dict]:
        """Generate sentences for tables"""
        
        prompt = f"""
Based on this table data:
{context}

Generate 2-3 sentences summarizing:
1. What data or information is presented
2. Key patterns, trends, or findings
3. The significance or implications

Focus on the most important insights from the data.

Sentences:"""
        
        return self._generate_with_ollama(prompt, 'table_analysis')
    
    def _generate_infographic_sentences(self, context: str, ocr_text: str, analysis: Dict) -> List[Dict]:
        """Generate sentences for infographics"""
        
        prompt = f"""
Based on this infographic:
{context}

Generate 2-3 sentences covering:
1. The main message or information being communicated
2. Key statistics, facts, or recommendations
3. The target audience or purpose

Make it informative and accessible.

Sentences:"""
        
        return self._generate_with_ollama(prompt, 'infographic_analysis')
    
    def _generate_generic_sentences(self, context: str, ocr_text: str, analysis: Dict) -> List[Dict]:
        """Generate sentences for generic visual content"""
        
        prompt = f"""
Based on this visual content:
{context}

Generate 1-2 descriptive sentences about:
1. What is shown in the image
2. The key information or message

Keep it clear and factual.

Sentences:"""
        
        return self._generate_with_ollama(prompt, 'generic_analysis')
    
    def _generate_with_ollama(self, prompt: str, analysis_type: str) -> List[Dict]:
        """Generate sentences using Ollama"""
        
        try:
            response = requests.post(self.ollama_url, json={
                "model": self.text_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.4,
                    "max_tokens": 200
                }
            }, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '').strip()
                
                # Split into sentences
                sentences = []
                for line in generated_text.split('\n'):
                    line = line.strip()
                    if line and len(line) > 10:
                        # Clean up numbering and formatting
                        line = re.sub(r'^\d+\.\s*', '', line)
                        line = line.strip('- ')
                        
                        if line:
                            sentences.append({
                                'text': line,
                                'source': 'visual_content',
                                'analysis_type': analysis_type,
                                'confidence': 0.8,
                                'generated_at': datetime.now().isoformat()
                            })
                
                return sentences
                
        except Exception as e:
            print(f"   ⚠️ Sentence generation failed: {e}")
        
        return []
    
    def _validate_generated_content(self, sentences: List[Dict]) -> List[Dict]:
        """Validate generated sentences for quality"""
        
        validated = []
        
        for sentence_data in sentences:
            sentence = sentence_data['text']
            
            # Basic validation criteria
            if (len(sentence) >= 15 and  # Minimum length
                len(sentence.split()) >= 4 and  # Minimum word count
                sentence[0].isupper() and  # Proper capitalization
                sentence.endswith(('.', '!', '?')) and  # Proper ending
                not sentence.startswith(('Figure', 'Table', 'Image'))):  # Not just references
                
                # Add validation score
                sentence_data['validation_score'] = 0.9
                sentence_data['validated'] = True
                validated.append(sentence_data)
        
        return validated

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python visual_intelligence_system.py <pdf_path>")
        sys.exit(1)
    
    system = VisualIntelligenceSystem()
    results = system.process_pdf_visuals(sys.argv[1])
    
    # Save results
    output_file = f"visual_intelligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_file}")
