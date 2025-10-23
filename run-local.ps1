# Run AI Bots Application Locally
# This script starts the backend application using ports from .env

Write-Host "🚀 Starting AI Bots Application Locally" -ForegroundColor Green
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    Write-Host "   Please copy .env.example to .env and configure your settings" -ForegroundColor Yellow
    exit 1
}

# Load .env file
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
}

# Get port from environment or default
$port = $env:APP_PORT
if (-not $port) {
    $port = 8000
}

$host_addr = $env:APP_HOST
if (-not $host_addr) {
    $host_addr = "localhost"
}

Write-Host "📋 Configuration:" -ForegroundColor Cyan
Write-Host "   • Backend Port: $port"
Write-Host "   • Backend Host: $host_addr"
Write-Host "   • Vector DB: $env:QDRANT_HOST:$env:QDRANT_PORT"
Write-Host ""
Write-Host "🌐 Access the API at: http://${host_addr}:${port}" -ForegroundColor Green
Write-Host "📚 API Docs at: http://${host_addr}:${port}/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the application
python main.py
