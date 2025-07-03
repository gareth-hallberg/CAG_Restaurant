#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found. Please create one with your OpenAI API key."
    exit 1
fi

# Install API requirements if needed
pip install -r requirements_api.txt

# Run the API
echo "🚀 Starting CAG System API on http://localhost:8000"
echo "📚 API Documentation available at http://localhost:8000/docs"
echo ""
uvicorn api:app --reload --host 0.0.0.0 --port 8000