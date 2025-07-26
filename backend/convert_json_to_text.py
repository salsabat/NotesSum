#!/usr/bin/env python3
"""
Convert existing JSON OCR results to text format
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.processors.text_formatter import convert_json_to_text

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Convert JSON OCR results to text format")
    parser.add_argument("input", type=Path, help="Input JSON file")
    parser.add_argument("-o", "--output", type=Path, help="Output text file")
    parser.add_argument("-f", "--format", choices=['readable', 'rag'], default='readable',
                       help="Output format: readable (default) or rag (optimized for RAG systems)")
    
    args = parser.parse_args()
    
    # Validate input
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        return 1
    
    if args.input.suffix.lower() != '.json':
        print("Error: Input file must be a JSON file")
        return 1
    
    # Set default output path
    if not args.output:
        if args.format == 'rag':
            args.output = args.input.with_suffix('.rag.txt')
        else:
            args.output = args.input.with_suffix('.txt')
    
    try:
        # Convert JSON to text
        print(f"Converting {args.input} to {args.format} format...")
        
        text_content = convert_json_to_text(str(args.input), args.format)
        
        # Save text file
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        print(f"✅ Conversion complete!")
        print(f"📄 Text file saved to: {args.output}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())