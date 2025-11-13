#!/usr/bin/env python
"""Script to run the FastAPI backend server."""
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "lanterne_rouge.backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
