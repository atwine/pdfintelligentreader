# PDF Intelligent Reader - Deployment Guide

## Overview

This guide covers deployment options for the PDF Intelligent Reader system, from development to production environments.

## Prerequisites

### System Requirements

- **CPU**: 2+ cores recommended (4+ for production)
- **RAM**: 4GB minimum (8GB+ for production)
- **Storage**: 10GB+ available space
- **OS**: Linux (Ubuntu 20.04+), macOS, or Windows 10+

### Software Dependencies

- **Python**: 3.9 or higher
- **Docker**: 20.10+ (for containerized deployment)
- **Docker Compose**: 1.29+ (for multi-container setup)

### External Services

- **OpenAI API**: Valid API key with GPT-4 access
- **Tesseract OCR**: For scanned document processing
- **spaCy Models**: English language model

## Deployment Options

### 1. Local Development

#### Quick Start

```bash
# Clone repository
git clone <repository-url>
cd pdfIntelligentReader

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Configure environment
cp .env.example .env
# Edit .env with your OpenAI API key

# Setup and run
python main.py setup
python main.py api --host 0.0.0.0 --port 8000
```

#### Development Server

```bash
# Run with auto-reload
python main.py api --reload

# Run tests
pytest tests/ -v

# Check code quality
black src/
mypy src/
```

### 2. Docker Deployment

#### Single Container

```bash
# Build image
docker build -t pdf-intelligent-reader .

# Run container
docker run -d \
  --name pdf-reader \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_api_key \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/output:/app/output \
  pdf-intelligent-reader
```

#### Docker Compose

```bash
# Create environment file
echo "OPENAI_API_KEY=your_api_key" > .env

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f pdf-reader-api

# Stop services
docker-compose down
```

### 3. Production Deployment

#### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml pdf-reader

# Scale services
docker service scale pdf-reader_api=3

# Update service
docker service update --image pdf-intelligent-reader:v2 pdf-reader_api
```

#### Using Kubernetes

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pdf-reader-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pdf-reader-api
  template:
    metadata:
      labels:
        app: pdf-reader-api
    spec:
      containers:
      - name: api
        image: pdf-intelligent-reader:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: pdf-reader-service
spec:
  selector:
    app: pdf-reader-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

```bash
# Deploy to Kubernetes
kubectl apply -f k8s-deployment.yaml

# Create secrets
kubectl create secret generic api-secrets \
  --from-literal=openai-api-key=your_api_key

# Check deployment
kubectl get pods
kubectl get services
```

## Environment Configuration

### Environment Variables

```bash
# Core Configuration
OPENAI_API_KEY=sk-...                    # Required: OpenAI API key
OPENAI_MODEL=gpt-4                       # OpenAI model to use
DATABASE_URL=sqlite:///./data/pdf_reader.db  # Database connection

# Processing Configuration
MAX_FILE_SIZE_MB=50                      # Maximum file size
BATCH_SIZE=10                           # Batch processing size
PROCESSING_TIMEOUT=300                   # Processing timeout (seconds)

# Quality Thresholds
MIN_SENTENCE_COMPLETENESS=0.95          # Minimum completeness score
MIN_TRANSLATION_READINESS=0.90          # Minimum translation readiness
MAX_NOISE_THRESHOLD=0.05                # Maximum noise threshold

# Logging Configuration
LOG_LEVEL=INFO                          # Logging level
LOG_FILE=logs/pdf_reader.log           # Log file path

# Development Settings
DEBUG=false                             # Debug mode
TESTING=false                           # Testing mode
```

### Production Environment

```bash
# Production-specific settings
DATABASE_URL=postgresql://user:pass@db:5432/pdf_reader
REDIS_URL=redis://redis:6379/0
LOG_LEVEL=WARNING
DEBUG=false

# Security settings
CORS_ORIGINS=https://yourdomain.com
API_KEY_REQUIRED=true
RATE_LIMIT_ENABLED=true

# Performance settings
WORKER_PROCESSES=4
MAX_CONCURRENT_SESSIONS=20
CACHE_TTL=3600
```

## Database Setup

### SQLite (Development)

```bash
# Automatic setup
python main.py setup
```

### PostgreSQL (Production)

```sql
-- Create database
CREATE DATABASE pdf_reader;
CREATE USER pdf_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE pdf_reader TO pdf_user;
```

```bash
# Set environment variable
export DATABASE_URL=postgresql://pdf_user:secure_password@localhost:5432/pdf_reader

# Initialize database
python -c "
from src.models.document import create_database
from src.config import settings
create_database(settings.database_url)
"
```

## Monitoring and Logging

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed status
curl http://localhost:8000/api/v1/stats
```

### Logging Configuration

```python
# Custom logging setup
import logging
from loguru import logger

# Configure structured logging
logger.add(
    "logs/app.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    level="INFO",
    rotation="100 MB",
    retention="30 days",
    compression="gz"
)
```

### Monitoring with Prometheus

```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  grafana_data:
```

## Performance Optimization

### Resource Allocation

```bash
# Docker resource limits
docker run -d \
  --name pdf-reader \
  --memory=2g \
  --cpus=2 \
  --restart=unless-stopped \
  pdf-intelligent-reader
```

### Caching Strategy

```python
# Redis caching configuration
REDIS_CONFIG = {
    'host': 'redis',
    'port': 6379,
    'db': 0,
    'decode_responses': True,
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
    'retry_on_timeout': True
}

# Cache processing results
CACHE_TTL = {
    'pdf_extraction': 3600,      # 1 hour
    'sentence_analysis': 1800,   # 30 minutes
    'quality_scores': 900        # 15 minutes
}
```

### Load Balancing

```nginx
# nginx.conf
upstream pdf_reader_backend {
    server pdf-reader-1:8000;
    server pdf-reader-2:8000;
    server pdf-reader-3:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://pdf_reader_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for processing
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }
    
    # File upload size limit
    client_max_body_size 100M;
}
```

## Security Configuration

### SSL/TLS Setup

```bash
# Generate SSL certificate (Let's Encrypt)
certbot --nginx -d your-domain.com

# Or use existing certificates
docker run -d \
  --name pdf-reader-ssl \
  -p 443:443 \
  -v /path/to/certs:/certs \
  -e SSL_CERT=/certs/cert.pem \
  -e SSL_KEY=/certs/key.pem \
  pdf-intelligent-reader
```

### API Security

```python
# API key authentication
API_KEYS = {
    'client1': 'api_key_1',
    'client2': 'api_key_2'
}

# Rate limiting
RATE_LIMITS = {
    'upload': '10/minute',
    'process': '5/minute',
    'status': '60/minute'
}

# CORS configuration
CORS_ORIGINS = [
    'https://yourdomain.com',
    'https://app.yourdomain.com'
]
```

### File Security

```bash
# Secure file permissions
chmod 750 uploads/
chmod 750 output/
chmod 640 .env

# User isolation
useradd -r -s /bin/false pdf-reader
chown -R pdf-reader:pdf-reader /app
```

## Backup and Recovery

### Database Backup

```bash
# SQLite backup
cp data/pdf_reader.db backups/pdf_reader_$(date +%Y%m%d_%H%M%S).db

# PostgreSQL backup
pg_dump -h localhost -U pdf_user pdf_reader > backups/pdf_reader_$(date +%Y%m%d_%H%M%S).sql
```

### File System Backup

```bash
# Backup uploads and output
tar -czf backups/files_$(date +%Y%m%d_%H%M%S).tar.gz uploads/ output/

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
cp data/pdf_reader.db $BACKUP_DIR/db_$DATE.db

# Files backup
tar -czf $BACKUP_DIR/files_$DATE.tar.gz uploads/ output/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

## Troubleshooting

### Common Issues

#### 1. OpenAI API Errors

```bash
# Check API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Verify quota
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/usage
```

#### 2. Memory Issues

```bash
# Monitor memory usage
docker stats pdf-reader

# Increase memory limit
docker update --memory=4g pdf-reader
```

#### 3. Processing Timeouts

```bash
# Check processing logs
docker logs pdf-reader | grep "timeout"

# Increase timeout
export PROCESSING_TIMEOUT=600
```

#### 4. File Upload Issues

```bash
# Check file permissions
ls -la uploads/

# Check disk space
df -h

# Check file size limits
curl -X POST -F "file=@large.pdf" http://localhost:8000/api/v1/upload
```

### Log Analysis

```bash
# View recent errors
tail -f logs/pdf_reader.log | grep ERROR

# Search for specific issues
grep "processing failed" logs/pdf_reader.log

# Monitor API requests
tail -f logs/pdf_reader.log | grep "POST\|GET"
```

### Performance Monitoring

```bash
# Check system resources
htop
iostat -x 1
free -h

# Monitor API performance
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8000/health
```

## Maintenance

### Regular Tasks

```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Clean temporary files
find temp/ -type f -mtime +1 -delete

# Rotate logs
logrotate /etc/logrotate.d/pdf-reader

# Update spaCy models
python -m spacy download en_core_web_sm --upgrade
```

### Health Monitoring

```python
# Health check script
#!/usr/bin/env python3
import requests
import sys

try:
    response = requests.get('http://localhost:8000/health', timeout=10)
    if response.status_code == 200:
        health = response.json()
        if health['status'] == 'healthy':
            print("✅ Service healthy")
            sys.exit(0)
    
    print("❌ Service unhealthy")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Health check failed: {e}")
    sys.exit(1)
```

## Scaling Considerations

### Horizontal Scaling

- Use load balancer (nginx, HAProxy)
- Implement session affinity if needed
- Scale database separately
- Use shared storage for files

### Vertical Scaling

- Increase CPU/memory allocation
- Optimize processing parameters
- Use faster storage (SSD)
- Tune database performance

### Auto-scaling

```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: pdf-reader-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: pdf-reader-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

This deployment guide provides comprehensive coverage of deployment scenarios from development to production, ensuring reliable and scalable operation of the PDF Intelligent Reader system.
