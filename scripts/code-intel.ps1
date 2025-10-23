#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Code Intelligence Orchestrator - PowerShell Wrapper

.DESCRIPTION
    Wrapper script to run code intelligence orchestrator from repository root.
    Ensures correct working directory and Python path.

.PARAMETER Command
    Command to run: embed, health, analyze, summarize, test

.PARAMETER Args
    Additional arguments to pass to orchestrator

.EXAMPLE
    .\code-intel.ps1 health
    .\code-intel.ps1 embed --log-level verbose
    .\code-intel.ps1 embed --force --max-files 100
#>

param(
    [Parameter(Position=0)]
    [string]$Command,
    
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

# Get script directory (should be repo root)
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Warning: .env file not found in repository root" -ForegroundColor Yellow
    Write-Host "   Copy .env.example to .env and configure Azure credentials" -ForegroundColor Yellow
    Write-Host ""
}

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠️  Warning: Virtual environment not activated" -ForegroundColor Yellow
    Write-Host "   Activate with: .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host ""
}

# Run orchestrator
$OrchestratorPath = Join-Path $RepoRoot "code-intelligence\orchestrator.py"

if ($Command) {
    python $OrchestratorPath $Command @Args
} else {
    # No command - show help
    python $OrchestratorPath --help
}
