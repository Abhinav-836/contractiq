# main.py - Root level entry point
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import the actual app
from apps.api.main import app

# This file will be used by uvicorn