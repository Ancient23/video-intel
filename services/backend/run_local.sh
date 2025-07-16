#!/bin/bash
# Script to run the backend with proper PYTHONPATH

# Set PYTHONPATH to the backend directory
export PYTHONPATH=/Users/filip/Documents/Source/video-intelligence-project/services/backend

# Run the FastAPI app
python -m uvicorn main:app --host 0.0.0.0 --port 8003 --reload