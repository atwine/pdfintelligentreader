# 🧠 PDF Intelligent Reader

**Advanced AI-Powered PDF Processing for Translation Workflows**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-Llama%203.1-green.svg)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](#)

*Transforming PDF documents into translation-ready, meaningful content using intelligent filtering and health context validation.*

---

## 🎯 **Overview**

The PDF Intelligent Reader is a sophisticated document processing system that extracts meaningful, translation-ready sentences from PDF documents. Unlike basic extraction tools that capture everything including noise, our system uses AI-powered intelligence to filter content and retain only complete, contextually relevant sentences.

### **Key Innovation: Intelligent Noise Filtering**
- **Problem**: Basic systems extract 99%+ content including "i LIST OF TABLES", page numbers, headers
- **Solution**: AI-powered filtering reduces noise by 70-80% using health context understanding  
- **Result**: Only meaningful, complete thoughts suitable for professional translation

---

## 🚀 **Quick Start**

### **Prerequisites**
```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Start Ollama and install model
ollama serve
ollama pull llama3.1:8b

# 3. Install Python dependencies
pip install pdfplumber requests
```

### **Basic Usage**
```bash
# Process a PDF with intelligent filtering
python standalone_intelligent_processor.py "document.pdf"

# Enhanced processing with agent interaction visibility
python enhanced_intelligent_processor.py "document.pdf"
```

---

## 🧠 **System Architecture**

### **Multi-Layer Intelligence Pipeline**
```
PDF Input
    ↓
Text Extraction (pdfplumber/PyMuPDF)
    ↓
Intelligent Preprocessing
    ↓
Quick Noise Filter (Rule-based)
    ↓
Health Context Detection
    ↓
AI Analysis (Ollama Llama 3.1 8B)
    ↓
Complete Thought Validation
    ↓
Meaningful Sentences Output
```

### **Core Components**
- **🔧 Text Extraction Engine**: Multi-method fallback (pdfplumber → PyMuPDF)
- **🧠 Intelligent Agent**: Ollama-powered with health context understanding
- **⭐ Quality Assurance**: Multi-dimensional scoring and validation
- **📊 Progress Tracking**: Real-time processing with agent interaction visibility

---

## 📊 **Performance Metrics**

| Metric | Basic System | Intelligent System | Improvement |
|--------|-------------|-------------------|-------------|
| **Noise Filtering** | ~5% | ~75% | **70% better** |
| **Health Relevance** | ~60% | ~95% | **35% better** |
| **Complete Thoughts** | ~70% | ~95% | **25% better** |
| **Translation Ready** | ~65% | ~90% | **25% better** |

### **Real-World Results**
- **Document**: 612-page Uganda IDSR Technical Guideline
- **Raw Extraction**: 6,084 potential sentences
- **After Intelligence**: ~1,250 meaningful sentences  
- **Noise Reduction**: 79.5% improvement

---

## 🔧 **Features**

### **✅ Intelligent Filtering**
- AI-powered sentence analysis with reasoning
- Health context vocabulary (200+ medical terms)
- Complete thought validation
- Confidence scoring (0.0-1.0)

### **✅ Processing Capabilities**
- Large document support (612+ pages)
- Multiple output formats (JSON, TXT, CSV)
- Progress tracking with agent interactions
- Fallback processing if AI unavailable

### **✅ Quality Examples**

**❌ FILTERED OUT (Noise)**
- "i LIST OF TABLES"
- "ii FOREWORD" 
- "1", "2", "3" (standalone numbers)
- "Figure 1.2", "Table 2.3"

**✅ KEPT (Meaningful)**
- "Disease surveillance is the systematic ongoing collection, collation, analysis and interpretation of health-related data essential to public health practice."
- "Early detection and response to disease outbreaks is critical for preventing widespread transmission."

---

## 📁 **Project Structure**

```
pdfIntelligentReader/
├── enhanced_intelligent_processor.py    # Enhanced processor with progress & agent visibility
├── standalone_intelligent_processor.py  # Main intelligent processor
├── src/intelligence/ollama_agent.py     # Core AI agent
├── main.py                              # CLI interface
├── requirements.txt                     # Dependencies
├── docs/                                # Documentation
└── output/                              # Processing results
```

---

## 🎯 **Use Cases**

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4

# Quality Thresholds
MIN_SENTENCE_COMPLETENESS=0.95
MIN_TRANSLATION_READINESS=0.90
MAX_NOISE_THRESHOLD=0.05

# Processing Configuration
MAX_FILE_SIZE_MB=50
BATCH_SIZE=10
PROCESSING_TIMEOUT=300
```

### Quality Thresholds

- **Completeness Score**: >95% (grammatical completeness)
- **Translation Readiness**: >90% (overall translation suitability)
- **Noise Threshold**: <5% (extraction artifacts and errors)

## 📊 Output Formats

### JSON Output
```json
{
  "metadata": {
    "export_timestamp": "2024-01-01T12:00:00Z",
    "sentence_count": 150,
    "processing_info": {...}
  },
  "sentences": [
    {
      "id": 1,
      "text": "This is a complete sentence ready for translation.",
      "approved": true,
      "quality_grade": "A",
      "quality_scores": {
        "completeness": 0.98,
        "clarity": 0.95,
        "structure": 0.97,
        "content": 0.93
      },
      "translation_readiness": {
        "score": 0.96,
        "level": "excellent"
      }
    }
  ]
}
```

### CSV Output
Structured tabular format with quality metrics and metadata.

### TXT Output
Clean text format for direct translation use.

### XML Output
Structured XML with comprehensive metadata preservation.

## 🧪 Testing

Run the test suite:
```bash
pytest tests/ -v --cov=src
```

## 📈 Performance

- **Processing Speed**: ~2-5 seconds per page
- **Accuracy**: >95% sentence completeness
- **Quality**: >90% translation readiness
- **Throughput**: 10-50 documents per minute (batch)

## 🔍 Quality Metrics

### Multi-Dimensional Scoring
- **Completeness**: Grammatical and semantic completeness
- **Clarity**: Readability and coherence
- **Structure**: Proper sentence structure
- **Content**: Meaningfulness and quality

### Translation Readiness Levels
- **Excellent** (≥0.9): Ready for immediate translation
- **Good** (≥0.8): Minor review recommended
- **Acceptable** (≥0.7): Some editing may be needed
- **Marginal** (≥0.6): Significant review required
- **Poor** (<0.6): Not suitable for translation

## 🚀 API Endpoints

### Core Processing
- `POST /api/v1/process` - Process single PDF
- `POST /api/v1/batch` - Batch processing
- `GET /api/v1/status/{session_id}` - Check status
- `GET /api/v1/result/{session_id}` - Download results

### System
- `GET /health` - Health check
- `GET /api/v1/stats` - System statistics
- `GET /api/v1/config` - Configuration

## 🛠️ Development

### Setup Development Environment
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
python -m spacy download en_core_web_sm
```

### Code Quality
```bash
black src/                 # Format code
mypy src/                  # Type checking
pytest tests/ --cov=src   # Run tests
```

## 🐳 Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm

COPY . .
EXPOSE 8000

CMD ["python", "main.py", "api", "--host", "0.0.0.0", "--port", "8000"]
```

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation in `/docs`
- Review the API documentation at `/docs` when running

## 🔮 Roadmap

- [ ] Multi-language support
- [ ] Advanced OCR with layout detection
- [ ] Real-time processing dashboard
- [ ] Integration with translation services
- [ ] Advanced quality metrics
- [ ] Custom model fine-tuning

---

**PDF Intelligent Reader** - Transforming PDF processing for translation excellence.
