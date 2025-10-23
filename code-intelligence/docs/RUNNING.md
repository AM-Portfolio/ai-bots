# Running Code Intelligence

## ⚠️ Important: Directory Context

The orchestrator must be run from the **repository root**, not from inside the `code-intelligence` directory.

### ✅ Correct Usage

```bash
# From repository root (ai-bots/)
cd A:\InfraCode\AM-Portfolio\ai-bots

# Then run orchestrator
python code-intelligence/orchestrator.py embed

# Or with Python module syntax
python -m code_intelligence.orchestrator embed
```

### ❌ Common Mistake

```bash
# DON'T do this - will fail to find .env
cd code-intelligence
python orchestrator.py embed  # ❌ Wrong! Can't find .env in parent dir
```

## Why This Matters

The orchestrator needs access to:
- `.env` file (in repository root)
- `shared/` modules (in repository root)
- Repository files to embed (in repository root)

When run from `code-intelligence/` directory:
- Can't find `.env` → Azure credentials missing
- Can't import `shared.config` → Import errors
- Wrong repository path → Embeds wrong files

## Quick Fix

If you're in the `code-intelligence` directory:

```bash
# Go back to repo root
cd ..

# Now run orchestrator
python code-intelligence/orchestrator.py embed
```

Or specify the repository path explicitly:

```bash
# From code-intelligence directory
python orchestrator.py embed --repo ..
```

## Complete Examples

### From Repository Root (Recommended)

```bash
# Navigate to repo root
cd A:\InfraCode\AM-Portfolio\ai-bots

# Check health
python code-intelligence/orchestrator.py health

# Embed repository
python code-intelligence/orchestrator.py embed

# With verbose logging
python code-intelligence/orchestrator.py embed --log-level verbose

# Force re-embed
python code-intelligence/orchestrator.py embed --force
```

### From Code-Intelligence Directory (Not Recommended)

```bash
cd A:\InfraCode\AM-Portfolio\ai-bots\code-intelligence

# Must specify parent as repo
python orchestrator.py embed --repo ..

# All commands need --repo ..
python orchestrator.py health --repo ..
python orchestrator.py analyze --repo ..
```

## Troubleshooting

### "Azure credentials not configured"
- **Cause**: .env file not found
- **Fix**: Run from repository root where .env exists

### "can't import shared.config"
- **Cause**: shared/ directory not in Python path
- **Fix**: Run from repository root, or add parent to PYTHONPATH

### "Not a git repository"
- **Cause**: Running from code-intelligence/ which isn't the git root
- **Fix**: Use `--repo ..` or run from repository root

### "Failed to initialize tree-sitter"
- **Cause**: tree-sitter-languages version issue
- **Fix**: This is a warning, can be ignored for now

## Best Practice

**Always create a wrapper script in repository root:**

```bash
# ai-bots/embed.sh
#!/bin/bash
python code-intelligence/orchestrator.py embed "$@"
```

```powershell
# ai-bots/embed.ps1
python code-intelligence/orchestrator.py embed $args
```

Then just run:
```bash
./embed.sh --log-level verbose
./embed.ps1 --force
```
