# AI Dev Agent - Full Application Startup Script
# Runs both Python backend and React frontend together

Write-Host "🚀 Starting AI Dev Agent Full Application..." -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# Set environment variables
$env:TOGETHER_API_KEY = "bff39f38ee07df9a08ff8d2e7279b9d7223ab3f283a30bc39590d36f77dbd2fd"
$env:GITHUB_TOKEN = "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"

Write-Host "✅ Environment variables set" -ForegroundColor Green

# Function to start backend
function Start-Backend {
    Write-Host "🐍 Starting Python Backend (Port 8000)..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; & '.venv\Scripts\Activate.ps1'; python main.py" -WindowStyle Normal
}

# Function to start frontend
function Start-Frontend {
    Write-Host "⚛️  Starting React Frontend (Port 5000)..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm run dev" -WindowStyle Normal
}

# Check if frontend dependencies are installed
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
    Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green
}

# Start applications
Write-Host "🚀 Launching applications..." -ForegroundColor Green
Start-Backend
Start-Sleep 3  # Wait for backend to initialize
Start-Frontend

Write-Host ""
Write-Host "🎉 Full-stack application is starting!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host "📍 Access URLs:" -ForegroundColor White
Write-Host "   🐍 Backend API:    http://localhost:8000" -ForegroundColor Yellow
Write-Host "   ⚛️  React Frontend: http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "📚 API Documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host "� Health Check:      http://localhost:8000/health" -ForegroundColor White
Write-Host "🌐 Main Application:  http://localhost:5000" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Press Ctrl+C in any terminal window to stop that service" -ForegroundColor Gray
Write-Host "=============================================" -ForegroundColor Green