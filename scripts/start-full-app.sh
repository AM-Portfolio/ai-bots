#!/bin/bash
# AI Dev Agent - Full Application Startup Script (Unix/Linux/Mac)
# Runs both Python backend and React frontend together

echo "🚀 Starting AI Dev Agent Full Application..."
echo "============================================="

# Set environment variables
export TOGETHER_API_KEY="bff39f38ee07df9a08ff8d2e7279b9d7223ab3f283a30bc39590d36f77dbd2fd"
export GITHUB_TOKEN="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"

echo "✅ Environment variables set"

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
    echo "✅ Frontend dependencies installed"
fi

# Start applications in background
echo "🐍 Starting Python Backend (Port 8000)..."
source .venv/bin/activate
python main.py &
BACKEND_PID=$!

sleep 3

echo "⚛️  Starting React Frontend (Port 5000)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

sleep 2

echo ""
echo "🎉 Full-stack application is running!"
echo "============================================="
echo "📍 Access URLs:"
echo "   🐍 Backend API:    http://localhost:8000"
echo "   ⚛️  React Frontend: http://localhost:5000"
echo ""
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check:      http://localhost:8000/health"
echo "🌐 Main Application:  http://localhost:5000"
echo ""
echo "💡 Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for all background processes
wait