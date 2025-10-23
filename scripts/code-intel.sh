#!/bin/bash
#
# Code Intelligence Orchestrator - Bash Wrapper
#
# Run code intelligence orchestrator from repository root.
# Ensures correct working directory and Python path.
#
# Usage:
#   ./code-intel.sh health
#   ./code-intel.sh embed --log-level verbose
#   ./code-intel.sh embed --force --max-files 100
#

# Get script directory (should be repo root)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found in repository root"
    echo "   Copy .env.example to .env and configure Azure credentials"
    echo ""
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Virtual environment not activated"
    echo "   Activate with: source .venv/bin/activate"
    echo ""
fi

# Run orchestrator
ORCHESTRATOR_PATH="$REPO_ROOT/code-intelligence/orchestrator.py"

if [ -n "$1" ]; then
    python "$ORCHESTRATOR_PATH" "$@"
else
    # No command - show help
    python "$ORCHESTRATOR_PATH" --help
fi
