#!/bin/bash

echo "🚀 Starting CAG Full Stack Application"
echo ""

# Function to cleanup on exit
cleanup() {
    echo "\n🛑 Shutting down services..."
    kill $API_PID $FRONTEND_PID 2>/dev/null
    exit
}

# Set trap for cleanup
trap cleanup INT TERM

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found. Please create one with your OpenAI API key."
    exit 1
fi

# Start API in background
echo "🔧 Starting API server..."
./run_api.sh &
API_PID=$!

# Wait for API to be ready
echo "⏳ Waiting for API to start..."
sleep 5

# Check if API is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ API failed to start. Check the logs above."
    exit 1
fi

echo "✅ API is running at http://localhost:8000"

# Start frontend
echo ""
echo "🎨 Starting frontend..."
cd frontend
npm install
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Full stack is starting!"
echo ""
echo "📍 API: http://localhost:8000"
echo "📍 API Docs: http://localhost:8000/docs"
echo "📍 Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for both processes
wait $API_PID $FRONTEND_PID