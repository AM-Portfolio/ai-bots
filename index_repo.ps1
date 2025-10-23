# Index the ai-bots repository with proper GitHub metadata
# Make sure your server is running first: python main.py

$apiUrl = "http://localhost:8000/api/code-intelligence/embed"
$body = @{
    github_repository = "AM-Portfolio/ai-bots"
    force_reindex = $true
    max_files = 100
    collection_name = "code_intelligence"
} | ConvertTo-Json

Write-Host "🚀 Starting repository indexing..." -ForegroundColor Cyan
Write-Host "📦 Repository: AM-Portfolio/ai-bots" -ForegroundColor Yellow
Write-Host "🔄 Force reindex: true" -ForegroundColor Yellow
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri $apiUrl -Method Post -Body $body -ContentType "application/json"
    
    Write-Host "✅ Indexing completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Results:" -ForegroundColor Cyan
    Write-Host "  • Success: $($response.success)" -ForegroundColor White
    Write-Host "  • Message: $($response.message)" -ForegroundColor White
    
    if ($response.stats) {
        Write-Host ""
        Write-Host "📈 Statistics:" -ForegroundColor Cyan
        $response.stats.PSObject.Properties | ForEach-Object {
            Write-Host "  • $($_.Name): $($_.Value)" -ForegroundColor White
        }
    }
}
catch {
    Write-Host "❌ Error during indexing:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Make sure the server is running: python main.py" -ForegroundColor Yellow
}
