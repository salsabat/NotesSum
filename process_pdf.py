#!/usr/bin/env python3
"""
Wrapper script for the Notes Summarizer backend
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run the backend main.py with all arguments passed through"""
    backend_main = Path(__file__).parent / "backend" / "main.py"
    
    # Pass all command line arguments to the backend script
    cmd = [sys.executable, str(backend_main)] + sys.argv[1:]
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        return e.returncode
    except FileNotFoundError:
        print(f"Error: Backend script not found at {backend_main}")
        return 1

if __name__ == "__main__":
    sys.exit(main())