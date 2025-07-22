#!/usr/bin/env python3
"""
Enhanced Setup Script for PDF Intelligent Reader
Comprehensive setup for production-ready system with visual intelligence
"""

import os
import sys
import subprocess
import platform
import requests
from pathlib import Path

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(step, description):
    """Print step information"""
    print(f"\n🔧 Step {step}: {description}")
    print("-" * 40)

def run_command(command, description=""):
    """Run command and handle errors"""
    try:
        if description:
            print(f"   Running: {description}")
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ Success: {description or command}")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"   ❌ Failed: {description or command}")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"❌ Python 3.9+ required. Current version: {version.major}.{version.minor}")
        return False
    
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def check_ollama_installation():
    """Check if Ollama is installed"""
    try:
        result = subprocess.run("ollama --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Ollama installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Ollama not found")
            return False
    except:
        print("❌ Ollama not found")
        return False

def check_tesseract_installation():
    """Check if Tesseract OCR is installed"""
    try:
        result = subprocess.run("tesseract --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Tesseract installed")
            return True
        else:
            print("❌ Tesseract not found")
            return False
    except:
        print("❌ Tesseract not found")
        return False

def install_python_dependencies():
    """Install Python dependencies"""
    print("   Installing Python packages...")
    
    packages = [
        "pdfplumber>=0.7.0",
        "PyMuPDF>=1.23.0", 
        "requests>=2.28.0",
        "opencv-python>=4.8.0",
        "pytesseract>=0.3.10",
        "Pillow>=10.0.0",
        "numpy>=1.24.0",
        "pytest>=7.4.0",
        "black>=23.0.0",
        "mypy>=1.6.0",
        "loguru>=0.7.0",
        "python-dotenv>=1.0.0"
    ]
    
    success_count = 0
    for package in packages:
        if run_command(f"pip install {package}", f"Installing {package.split('>=')[0]}"):
            success_count += 1
    
    print(f"\n   📦 Installed {success_count}/{len(packages)} packages")
    return success_count == len(packages)

def setup_ollama_models():
    """Setup required Ollama models"""
    models = [
        ("llama3.1:8b", "Text processing and reasoning"),
        ("llava:7b", "Visual content analysis")
    ]
    
    for model, description in models:
        print(f"   Setting up {model} ({description})...")
        if run_command(f"ollama pull {model}", f"Downloading {model}"):
            print(f"   ✅ {model} ready")
        else:
            print(f"   ⚠️ {model} download may be in progress")

def check_ollama_service():
    """Check if Ollama service is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama service is running")
            models = response.json().get('models', [])
            print(f"   Available models: {len(models)}")
            for model in models:
                print(f"   - {model.get('name', 'Unknown')}")
            return True
        else:
            print("❌ Ollama service not responding")
            return False
    except:
        print("❌ Ollama service not accessible")
        print("   Start with: ollama serve")
        return False

def create_directory_structure():
    """Create necessary directories"""
    directories = [
        "uploads",
        "output", 
        "logs",
        "tests",
        "docs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   ✅ Created/verified: {directory}/")

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# PDF Intelligent Reader Configuration

# Ollama Configuration
OLLAMA_URL=http://localhost:11434/api/generate
TEXT_MODEL=llama3.1:8b
VISION_MODEL=llava:7b

# Processing Configuration
MAX_SENTENCES_PER_BATCH=100
DEFAULT_CONFIDENCE_THRESHOLD=0.7
ENABLE_VISUAL_PROCESSING=true

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/pdf_processor.log

# Output Configuration
DEFAULT_OUTPUT_FORMAT=json
INCLUDE_REASONING=true
INCLUDE_PARAPHRASES=true
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("   ✅ Created .env configuration file")
    else:
        print("   ✅ .env file already exists")

def run_system_tests():
    """Run basic system tests"""
    print("   Running system validation tests...")
    
    # Test imports
    test_imports = [
        "import pdfplumber",
        "import fitz",
        "import cv2", 
        "import PIL",
        "import pytesseract",
        "import numpy",
        "import requests"
    ]
    
    success_count = 0
    for test_import in test_imports:
        try:
            exec(test_import)
            module_name = test_import.split()[1]
            print(f"   ✅ {module_name} import successful")
            success_count += 1
        except Exception as e:
            module_name = test_import.split()[1]
            print(f"   ❌ {module_name} import failed: {e}")
    
    print(f"\n   📊 Import tests: {success_count}/{len(test_imports)} passed")
    return success_count == len(test_imports)

def display_installation_guide():
    """Display installation guide for missing components"""
    print_header("INSTALLATION GUIDE")
    
    print("\n🔧 MISSING COMPONENTS INSTALLATION:")
    
    print("\n1. OLLAMA INSTALLATION:")
    if platform.system() == "Windows":
        print("   Download from: https://ollama.ai/download/windows")
        print("   Or use: winget install Ollama.Ollama")
    elif platform.system() == "Darwin":  # macOS
        print("   brew install ollama")
    else:  # Linux
        print("   curl -fsSL https://ollama.ai/install.sh | sh")
    
    print("\n2. TESSERACT OCR INSTALLATION:")
    if platform.system() == "Windows":
        print("   Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("   Add to PATH: C:\\Program Files\\Tesseract-OCR")
    elif platform.system() == "Darwin":  # macOS
        print("   brew install tesseract")
    else:  # Linux
        print("   sudo apt-get install tesseract-ocr")
        print("   sudo yum install tesseract")
    
    print("\n3. START SERVICES:")
    print("   ollama serve                    # Start Ollama service")
    print("   ollama pull llama3.1:8b         # Download text model")
    print("   ollama pull llava:7b            # Download vision model")

def main():
    """Main setup function"""
    print_header("PDF INTELLIGENT READER - ENHANCED SETUP")
    print("🚀 Setting up production-ready system with visual intelligence")
    
    # Step 1: Check Python version
    print_step(1, "Checking Python version")
    if not check_python_version():
        print("❌ Setup failed: Python 3.9+ required")
        return False
    
    # Step 2: Check system dependencies
    print_step(2, "Checking system dependencies")
    ollama_ok = check_ollama_installation()
    tesseract_ok = check_tesseract_installation()
    
    # Step 3: Install Python dependencies
    print_step(3, "Installing Python dependencies")
    python_deps_ok = install_python_dependencies()
    
    # Step 4: Create directory structure
    print_step(4, "Setting up directory structure")
    create_directory_structure()
    
    # Step 5: Create configuration
    print_step(5, "Creating configuration files")
    create_env_file()
    
    # Step 6: Setup Ollama models (if Ollama is available)
    if ollama_ok:
        print_step(6, "Setting up Ollama models")
        setup_ollama_models()
        
        print_step(7, "Checking Ollama service")
        ollama_service_ok = check_ollama_service()
    else:
        ollama_service_ok = False
    
    # Step 7: Run system tests
    print_step(8, "Running system validation")
    tests_ok = run_system_tests()
    
    # Final status
    print_header("SETUP COMPLETE")
    
    print(f"✅ Python dependencies: {'OK' if python_deps_ok else 'FAILED'}")
    print(f"✅ Ollama installation: {'OK' if ollama_ok else 'MISSING'}")
    print(f"✅ Tesseract OCR: {'OK' if tesseract_ok else 'MISSING'}")
    print(f"✅ Ollama service: {'OK' if ollama_service_ok else 'NOT RUNNING'}")
    print(f"✅ System tests: {'OK' if tests_ok else 'FAILED'}")
    
    if all([python_deps_ok, ollama_ok, tesseract_ok, ollama_service_ok, tests_ok]):
        print("\n🎉 SETUP SUCCESSFUL! System ready for production use.")
        print("\n🚀 QUICK START:")
        print("   python advanced_reasoning_processor.py \"document.pdf\"")
        print("   python visual_intelligence_system.py \"document.pdf\"")
        print("   python trial_run.py \"document.pdf\"")
        return True
    else:
        print("\n⚠️ SETUP INCOMPLETE - Some components need attention")
        if not ollama_ok or not tesseract_ok:
            display_installation_guide()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
