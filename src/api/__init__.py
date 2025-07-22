"""
FastAPI backend for PDF Intelligent Reader
"""

from .main import app
from .models import *
from .endpoints import *

__all__ = ["app"]
