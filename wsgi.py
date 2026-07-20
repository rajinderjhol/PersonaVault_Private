import os
import sys

# Add the backend root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.main import create_app

app = create_app()