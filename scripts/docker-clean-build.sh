#!/bin/bash
# Docker Clean and Build Script for Linux/Mac
# This script cleans Docker cache and builds containers efficiently

echo "🧹 Docker Clean and Build Process"
echo "================================="
echo ""

# Stop and remove existing containers
echo "⏹️  Stopping existing containers..."
docker-compose -f docker-compose.app.yml down 2>/dev/null
echo "✅ Containers stopped"
echo ""

# Prompt for clean level
echo "Select clean level:"
echo "1. Quick clean (remove only app containers)"
echo "2. Full clean (remove containers + build cache)"
echo "3. Deep clean (remove everything including images)"
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo "🔄 Quick clean - removing containers only..."
        ;;
    2)
        echo "🧹 Full clean - removing build cache..."
        docker builder prune -f
        echo "✅ Build cache cleared"
        ;;
    3)
        echo "💥 Deep clean - removing images and cache..."
        docker rmi ai-bots-backend:latest 2>/dev/null
        docker rmi ai-bots-frontend:latest 2>/dev/null
        docker builder prune -af
        echo "✅ Images and cache cleared"
        ;;
esac
echo ""

# Build containers in parallel
echo "🏗️  Building containers..."
echo "   This may take a few minutes on first build..."
echo ""

build_start=$(date +%s)
docker-compose -f docker-compose.app.yml build --parallel

if [ $? -eq 0 ]; then
    build_end=$(date +%s)
    build_time=$((build_end - build_start))
    echo ""
    echo "✅ Build completed successfully in $build_time seconds"
    echo ""
    
    # Start containers
    echo "🚀 Starting containers..."
    docker-compose -f docker-compose.app.yml up -d
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Containers started successfully!"
        echo ""
        echo "📊 Container Status:"
        docker-compose -f docker-compose.app.yml ps
        echo ""
        echo "🌐 Access your services:"
        echo "   Frontend: http://localhost:4000"
        echo "   Backend:  http://localhost:9000"
        echo "   API Docs: http://localhost:9000/docs"
        echo ""
        echo "📝 View logs with: docker-compose -f docker-compose.app.yml logs -f"
    else
        echo "❌ Failed to start containers"
        exit 1
    fi
else
    echo ""
    echo "❌ Build failed"
    exit 1
fi
