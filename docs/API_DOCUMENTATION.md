# PDF Intelligent Reader API Documentation

## Overview

The PDF Intelligent Reader API provides intelligent PDF text extraction and sentence processing capabilities optimized for translation workflows. The API uses a multi-agent CrewAI architecture to ensure high-quality, translation-ready output.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required. In production, implement appropriate authentication mechanisms.

## Core Endpoints

### 1. Health Check

**GET** `/health`

Check the health status of the API and its components.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "components": {
    "database": "healthy",
    "pdf_crew": "healthy",
    "storage": "healthy",
    "openai": "healthy"
  }
}
```

### 2. Upload PDF

**POST** `/api/v1/upload`

Upload a PDF file for processing.

**Request:**
- Content-Type: `multipart/form-data`
- Body: PDF file

**Response:**
```json
{
  "file_id": "uuid-string",
  "filename": "document.pdf",
  "file_path": "uploads/uuid-string.pdf",
  "file_size": 1024000,
  "message": "File uploaded successfully"
}
```

### 3. Process PDF

**POST** `/api/v1/process`

Process a PDF file through the complete pipeline.

**Request:**
- Content-Type: `multipart/form-data`
- Body: PDF file + processing options

**Processing Options:**
```json
{
  "output_format": "json",        // json, csv, txt, xml
  "approved_only": true,          // Export only approved sentences
  "include_metadata": true,       // Include processing metadata
  "preserve_context": true        // Preserve sentence context
}
```

**Response:**
```json
{
  "success": true,
  "message": "Processing started",
  "session_id": "uuid-string"
}
```

### 4. Check Processing Status

**GET** `/api/v1/status/{session_id}`

Check the status of a processing session.

**Response:**
```json
{
  "session_id": "uuid-string",
  "status": "processing",         // pending, processing, completed, failed
  "progress": 0.75,              // 0.0 to 1.0
  "message": "Processing sentences",
  "started_at": "2024-01-01T12:00:00Z",
  "completed_at": null,
  "error": null
}
```

### 5. Get Processing Results

**GET** `/api/v1/result/{session_id}`

Retrieve the results of a completed processing session.

**Response:**
- If output file exists: File download
- Otherwise: JSON response with processing results

**JSON Response Example:**
```json
{
  "success": true,
  "summary": {
    "total_sentences": 150,
    "approved_sentences": 142,
    "rejected_sentences": 8,
    "approval_rate": 0.947,
    "average_quality_score": 0.89,
    "processing_time": 12.5,
    "extraction_method": "pymupdf",
    "language_detected": "en"
  },
  "sentences": [
    {
      "id": 1,
      "text": "This is a complete sentence ready for translation.",
      "approved": true,
      "quality_grade": "A",
      "word_count": 9,
      "confidence": 0.95,
      "completeness_score": 0.98,
      "clarity_score": 0.95,
      "structure_score": 0.97,
      "content_score": 0.93,
      "translation_readiness_score": 0.96,
      "needs_context": false,
      "issues_count": 0
    }
  ]
}
```

### 6. System Statistics

**GET** `/api/v1/stats`

Get system-wide processing statistics.

**Response:**
```json
{
  "total_documents_processed": 1250,
  "total_sentences_extracted": 45000,
  "average_processing_time": 8.5,
  "success_rate": 0.96,
  "most_common_language": "en",
  "uptime_hours": 168.5
}
```

### 7. Configuration

**GET** `/api/v1/config`

Get current processing configuration and thresholds.

**Response:**
```json
{
  "max_file_size_mb": 50,
  "batch_size": 10,
  "processing_timeout": 300,
  "quality_thresholds": {
    "min_completeness": 0.95,
    "min_translation_readiness": 0.90,
    "max_noise_threshold": 0.05
  }
}
```

## Batch Processing

### Process Multiple PDFs

**POST** `/api/v1/batch`

Process multiple PDF files in a batch operation.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Multiple PDF files + batch options

**Response:**
```json
{
  "success": true,
  "message": "Batch processing started",
  "batch_id": "uuid-string",
  "total_files": 5,
  "estimated_completion": "2024-01-01T12:15:00Z"
}
```

### Check Batch Status

**GET** `/api/v1/batch/{batch_id}/status`

Check the status of a batch processing operation.

**Response:**
```json
{
  "batch_id": "uuid-string",
  "status": "processing",
  "total_files": 5,
  "processed_files": 3,
  "failed_files": 0,
  "progress": 0.6,
  "estimated_completion": "2024-01-01T12:10:00Z"
}
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error description",
  "error_code": "400",
  "details": {
    "field": "Additional error details"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Common Error Codes

- **400**: Bad Request - Invalid input parameters
- **413**: Payload Too Large - File exceeds size limit
- **404**: Not Found - Session or resource not found
- **429**: Too Many Requests - Rate limit exceeded
- **500**: Internal Server Error - Processing failure

## Rate Limits

- **File Upload**: 10 requests per minute
- **Processing**: 5 concurrent sessions per client
- **Status Checks**: 60 requests per minute

## File Size Limits

- **Maximum file size**: 50MB (configurable)
- **Supported formats**: PDF only
- **Batch limit**: 20 files per batch

## Quality Metrics

### Quality Scores (0.0 - 1.0)

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

### Quality Grades

- **A**: Excellent quality (≥0.9)
- **B**: Good quality (≥0.8)
- **C**: Acceptable quality (≥0.7)
- **F**: Failed quality checks (<0.7)

## Output Formats

### JSON
Structured format with complete metadata and quality scores.

### CSV
Tabular format suitable for spreadsheet analysis.

### TXT
Plain text format for direct translation use.

### XML
Structured XML with comprehensive metadata preservation.

## Usage Examples

### Python Client Example

```python
import requests
import time

# Upload and process PDF
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/process',
        files={'file': f},
        data={
            'output_format': 'json',
            'approved_only': True,
            'include_metadata': True
        }
    )

session_id = response.json()['session_id']

# Check status
while True:
    status_response = requests.get(f'http://localhost:8000/api/v1/status/{session_id}')
    status = status_response.json()
    
    if status['status'] == 'completed':
        break
    elif status['status'] == 'failed':
        print(f"Processing failed: {status['error']}")
        break
    
    time.sleep(5)

# Get results
result_response = requests.get(f'http://localhost:8000/api/v1/result/{session_id}')
results = result_response.json()

print(f"Processed {results['summary']['total_sentences']} sentences")
print(f"Approval rate: {results['summary']['approval_rate']:.1%}")
```

### cURL Examples

```bash
# Health check
curl http://localhost:8000/health

# Upload and process PDF
curl -X POST "http://localhost:8000/api/v1/process" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf" \
  -F "output_format=json" \
  -F "approved_only=true"

# Check status
curl "http://localhost:8000/api/v1/status/session-id"

# Download results
curl "http://localhost:8000/api/v1/result/session-id" -o results.json
```

## WebSocket Support (Future)

Real-time processing updates will be available via WebSocket connections:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/processing/session-id');
ws.onmessage = function(event) {
    const update = JSON.parse(event.data);
    console.log(`Progress: ${update.progress * 100}%`);
};
```

## SDK and Libraries

Official SDKs are planned for:
- Python
- JavaScript/Node.js
- Java
- C#

## Support

For API support:
- Documentation: `/docs` (Swagger UI)
- ReDoc: `/redoc`
- Issues: GitHub repository
- Email: support@example.com
