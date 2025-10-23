# Verify the indexing by checking collection stats and querying

$apiUrl = "http://localhost:8000/api/code-intelligence"

Write-Host "🔍 Verifying repository indexing..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Check collection stats
Write-Host "📊 Step 1: Checking collection statistics..." -ForegroundColor Yellow
try {
    $statsResponse = Invoke-RestMethod -Uri "$apiUrl/stats?collection_name=code_intelligence" -Method Get
    
    Write-Host "✅ Collection stats retrieved!" -ForegroundColor Green
    Write-Host "  • Collection: $($statsResponse.collection_name)" -ForegroundColor White
    Write-Host "  • Total vectors: $($statsResponse.vectors_count)" -ForegroundColor White
    Write-Host "  • Status: $($statsResponse.status)" -ForegroundColor White
    Write-Host ""
}
catch {
    Write-Host "❌ Could not get stats: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Step 2: Test query to verify data
Write-Host "🔎 Step 2: Testing query to verify indexed data..." -ForegroundColor Yellow
$queryBody = @{
    query = "API implementation"
    limit = 3
    collection_name = "code_intelligence"
} | ConvertTo-Json

try {
    $queryResponse = Invoke-RestMethod -Uri "$apiUrl/query" -Method Post -Body $queryBody -ContentType "application/json"
    
    Write-Host "✅ Query successful!" -ForegroundColor Green
    Write-Host "  • Found results: $($queryResponse.total_results)" -ForegroundColor White
    Write-Host ""
    
    if ($queryResponse.results -and $queryResponse.results.Count -gt 0) {
        Write-Host "📋 Sample Results:" -ForegroundColor Cyan
        $queryResponse.results | Select-Object -First 3 | ForEach-Object {
            $payload = $_.payload
            Write-Host "  ---" -ForegroundColor DarkGray
            Write-Host "  • File: $($payload.file_path)" -ForegroundColor White
            Write-Host "  • Repo: $($payload.repo_name)" -ForegroundColor White
            Write-Host "  • Source: $($payload.source)" -ForegroundColor White
            Write-Host "  • Score: $($_.score)" -ForegroundColor White
        }
        Write-Host ""
        
        # Check if repo_name is populated
        $firstResult = $queryResponse.results[0]
        if ($firstResult.payload.repo_name) {
            Write-Host "✅ SUCCESS: repo_name is properly set to '$($firstResult.payload.repo_name)'" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️  WARNING: repo_name is null - reindexing may be needed" -ForegroundColor Yellow
            Write-Host "💡 Run: .\index_repo.ps1 to reindex with proper metadata" -ForegroundColor Cyan
        }
    }
}
catch {
    Write-Host "❌ Query failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "🏁 Verification complete!" -ForegroundColor Cyan
