# Docker Clean and Build Script for Windows
# This script cleans Docker cache and builds containers efficiently

Write-Host "🧹 Docker Clean and Build Process" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Stop and remove existing containers
Write-Host "⏹️  Stopping existing containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.app.yml down 2>$null
Write-Host "✅ Containers stopped" -ForegroundColor Green
Write-Host ""

# Prompt for clean level
Write-Host "Select clean level:" -ForegroundColor Cyan
Write-Host "1. Quick clean (remove only app containers)"
Write-Host "2. Full clean (remove containers + build cache)"
Write-Host "3. Deep clean (remove everything including images)"
$choice = Read-Host "Enter choice (1-3)"

switch ($choice) {
    "1" {
        Write-Host "🔄 Quick clean - removing containers only..." -ForegroundColor Yellow
    }
    "2" {
        Write-Host "🧹 Full clean - removing build cache..." -ForegroundColor Yellow
        docker builder prune -f
        Write-Host "✅ Build cache cleared" -ForegroundColor Green
    }
    "3" {
        Write-Host "💥 Deep clean - removing images and cache..." -ForegroundColor Yellow
        docker rmi ai-bots-backend:latest 2>$null
        docker rmi ai-bots-frontend:latest 2>$null
        docker builder prune -af
        Write-Host "✅ Images and cache cleared" -ForegroundColor Green
    }
}
Write-Host ""

# Build containers in parallel
Write-Host "🏗️  Building containers..." -ForegroundColor Cyan
Write-Host "   This may take a few minutes on first build..." -ForegroundColor Gray
Write-Host ""

$buildStart = Get-Date
docker-compose -f docker-compose.app.yml build --parallel

if ($LASTEXITCODE -eq 0) {
    $buildTime = [math]::Round(((Get-Date) - $buildStart).TotalSeconds, 2)
    Write-Host ""
    Write-Host "✅ Build completed successfully in $buildTime seconds" -ForegroundColor Green
    Write-Host ""
    
    # Start containers
    Write-Host "🚀 Starting containers..." -ForegroundColor Cyan
    docker-compose -f docker-compose.app.yml up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Containers started successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📊 Container Status:" -ForegroundColor Cyan
        docker-compose -f docker-compose.app.yml ps
        Write-Host ""
        Write-Host "🌐 Access your services:" -ForegroundColor Cyan
        Write-Host "   Frontend: http://localhost:4000" -ForegroundColor White
        Write-Host "   Backend:  http://localhost:9000" -ForegroundColor White
        Write-Host "   API Docs: http://localhost:9000/docs" -ForegroundColor White
        Write-Host ""
        Write-Host "📝 View logs with: docker-compose -f docker-compose.app.yml logs -f" -ForegroundColor Gray
    } else {
        Write-Host "❌ Failed to start containers" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "❌ Build failed" -ForegroundColor Red
    exit 1
}
