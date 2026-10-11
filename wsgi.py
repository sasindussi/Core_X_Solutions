import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app

if __name__ == "__main__":
    app.run()
