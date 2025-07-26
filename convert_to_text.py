#!/usr/bin/env python3
"""
Wrapper script for the JSON to text converter
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run the backend convert_json_to_text.py with all arguments passed through"""
    backend_converter = Path(__file__).parent / "backend" / "convert_json_to_text.py"
    
    # Pass all command line arguments to the backend script
    cmd = [sys.executable, str(backend_converter)] + sys.argv[1:]
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        return e.returncode
    except FileNotFoundError:
        print(f"Error: Backend script not found at {backend_converter}")
        return 1

if __name__ == "__main__":
    sys.exit(main())