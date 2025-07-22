#!/usr/bin/env python3
"""
PDF Intelligent Reader - Setup and Installation Script
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def install_dependencies():
    """Install Python dependencies"""
    commands = [
        ("pip install -r requirements.txt", "Installing Python dependencies"),
        ("python -m spacy download en_core_web_sm", "Installing spaCy English model"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    return True


def setup_environment():
    """Setup environment and directories"""
    directories = ["logs", "uploads", "output", "temp", "data"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Create .env file if it doesn't exist
    if not Path(".env").exists():
        print("📝 Creating .env file from template...")
        try:
            with open(".env.example", "r") as source:
                content = source.read()
            with open(".env", "w") as target:
                target.write(content)
            print("✅ .env file created - Please add your OpenAI API key")
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    
    return True


def initialize_database():
    """Initialize the database"""
    try:
        sys.path.insert(0, str(Path.cwd() / "src"))
        from src.models.document import create_database
        from src.config import settings
        
        create_database(settings.database_url)
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


def run_basic_test():
    """Run basic functionality test"""
    try:
        sys.path.insert(0, str(Path.cwd() / "src"))
        from src.tools.pdf_extractor import PDFExtractor
        
        extractor = PDFExtractor()
        confidence = extractor._calculate_text_confidence("This is a test sentence.")
        
        if confidence > 0:
            print("✅ Basic functionality test passed")
            return True
        else:
            print("❌ Basic functionality test failed")
            return False
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False


def main():
    """Main setup function"""
    print("🚀 PDF Intelligent Reader - Setup Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Dependency installation failed")
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("❌ Environment setup failed")
        sys.exit(1)
    
    # Initialize database
    if not initialize_database():
        print("❌ Database initialization failed")
        sys.exit(1)
    
    # Run basic test
    if not run_basic_test():
        print("❌ Basic functionality test failed")
        sys.exit(1)
    
    print("=" * 50)
    print("🎉 Setup completed successfully!")
    print()
    print("📋 Next Steps:")
    print("1. Add your OpenAI API key to the .env file")
    print("2. Test with: python main.py process sample.pdf")
    print("3. Start API server: python main.py api")
    print("4. Or use Docker: docker-compose up -d")
    print()
    print("📚 Documentation:")
    print("- README.md - Complete usage guide")
    print("- docs/API_DOCUMENTATION.md - API reference")
    print("- docs/DEPLOYMENT_GUIDE.md - Deployment guide")


if __name__ == "__main__":
    main()
