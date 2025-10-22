#!/usr/bin/env python3
"""
Code Intelligence CLI Wrapper

Run this from the repository root, not from code-intelligence directory:
  
  python code-intelligence/cli.py embed
  
Or add code-intelligence to your PATH and run:
  
  cli.py embed
"""

import sys
import os
from pathlib import Path

# Ensure we're running from the correct directory
current_dir = Path.cwd()
script_dir = Path(__file__).parent

# Check if we're in the code-intelligence directory
if current_dir.name == "code-intelligence":
    print("❌ Error: Don't run from inside code-intelligence directory")
    print()
    print("✅ Instead, run from the repository root:")
    print(f"   cd ..")
    print(f"   python code-intelligence/orchestrator.py embed")
    print()
    print("Or specify the repository path:")
    print(f"   python orchestrator.py embed --repo ..")
    sys.exit(1)

# Add parent directory to path
sys.path.insert(0, str(script_dir.parent))

# Import and run the orchestrator
from code_intelligence.orchestrator import main

if __name__ == "__main__":
    main()
