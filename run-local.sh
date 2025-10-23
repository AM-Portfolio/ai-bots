#!/bin/bash
# Run AI Bots Application Locally
# This script starts the backend application using ports from .env

echo "🚀 Starting AI Bots Application Locally"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "   Please copy .env.example to .env and configure your settings"
    exit 1
fi

# Load .env file
export $(grep -v '^#' .env | xargs)

# Get port from environment or default
PORT=${APP_PORT:-8000}
HOST=${APP_HOST:-localhost}

echo "📋 Configuration:"
echo "   • Backend Port: $PORT"
echo "   • Backend Host: $HOST"
echo "   • Vector DB: $QDRANT_HOST:$QDRANT_PORT"
echo ""
echo "🌐 Access the API at: http://${HOST}:${PORT}"
echo "📚 API Docs at: http://${HOST}:${PORT}/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the application
python main.py
