#!/usr/bin/env python3
"""
Notes Summarizer with Advanced OCR
Main application demonstrating the document processing system
"""

import argparse
import logging
from pathlib import Path
import sys
from typing import List, Dict, Any
import numpy as np
# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from parsing.src.config import settings
from parsing.src.extractors.text_extractor import TextExtractor
from parsing.src.extractors.table_extractor import TableExtractor
from parsing.src.processors.text_formatter import TextFormatter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Main document processor that coordinates all extractors"""
    
    def __init__(self):
        self.text_extractor = TextExtractor()
        self.table_extractor = TableExtractor()
        self.text_formatter = TextFormatter()
        logger.info("Document processor initialized with full OCR capabilities")
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        Extract text directly from PDF text layers (fast path)
        Falls back to OCR if no text is found
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text as string
        """
        logger.info(f"Attempting direct text extraction from PDF: {pdf_path}")
        
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            text_content = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                if page_text.strip():
                    text_content += page_text + "\n"
            
            doc.close()
            
            # Check if we got meaningful text
            if text_content.strip():
                logger.info(f"Successfully extracted {len(text_content)} characters directly from PDF text layers")
                return text_content.strip()
            else:
                logger.info("No text found in PDF text layers, falling back to OCR")
                return None
                
        except ImportError:
            logger.warning("PyMuPDF not available, falling back to OCR")
            return None
        except Exception as e:
            logger.warning(f"Direct text extraction failed: {e}, falling back to OCR")
            return None
    
    def process_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Process a PDF file and extract all content
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary containing extracted content
        """
        logger.info(f"Processing PDF: {pdf_path}")
        
        direct_text = self.extract_text_from_pdf(pdf_path)
        
        if direct_text:
            logger.info("Using direct text extraction (fast path)")
            return {
                'file_path': str(pdf_path),
                'pages': [{
                    'page_number': 1,
                    'regions': [{
                        'type': 'text',
                        'content': direct_text,
                        'confidence': 1.0,
                        'word_boxes': [],
                        'word_count': len(direct_text.split()),
                        'line_count': len(direct_text.split('\n')),
                        'extractor': 'PyMuPDF'
                    }],
                    'region_count': 1
                }],
                'summary': {
                    'total_pages': 1,
                    'text_regions': 1,
                    'tables': 0,
                    'equations': 0,
                    'diagrams': 0
                }
            }
        
        logger.info("No text layers found, using OCR processing")
        try:
            return self._process_pdf_with_ocr(pdf_path)
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return {
                'file_path': str(pdf_path),
                'pages': [{
                    'page_number': 1,
                    'regions': [{
                        'type': 'text',
                        'content': f"OCR processing failed: {str(e)}",
                        'confidence': 0.0,
                        'extractor': 'Error'
                    }],
                    'region_count': 1
                }],
                'summary': {
                    'total_pages': 1,
                    'text_regions': 1,
                    'tables': 0,
                    'equations': 0,
                    'diagrams': 0
                }
            }
    
    def _process_pdf_with_ocr(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Process a PDF file using OCR (original method)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary containing extracted content
        """
        images = self._pdf_to_images(pdf_path)
        
        results = {
            'file_path': str(pdf_path),
            'pages': [],
            'summary': {
                'total_pages': len(images),
                'text_regions': 0,
                'tables': 0,
                'equations': 0,
                'diagrams': 0
            }
        }
        
        for page_num, image in enumerate(images, 1):
            logger.info(f"Processing page {page_num}/{len(images)}")
            
            page_result = self._process_page(image, page_num)
            results['pages'].append(page_result)
            
            for region in page_result['regions']:
                region_type = region.get('type', 'unknown')
                if region_type in results['summary']:
                    results['summary'][region_type] += 1
        
        logger.info(f"OCR processing complete. Found {results['summary']}")
        return results
    
    def _pdf_to_images(self, pdf_path: Path) -> List:
        """Convert PDF to list of images"""
        try:
            from pdf2image import convert_from_path
            
            images = convert_from_path(
                pdf_path,
                dpi=settings.DPI,
                fmt='RGB'
            )
            
            logger.info(f"Converted PDF to {len(images)} images using pdf2image")
            return images
            
        except ImportError:
            logger.warning("pdf2image not installed. Trying PyMuPDF fallback...")
        except Exception as e:
            logger.warning(f"pdf2image failed: {e}. Trying PyMuPDF fallback...")
        
        try:
            import fitz  # PyMuPDF
            from PIL import Image
            import io
            
            doc = fitz.open(pdf_path)
            images = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                mat = fitz.Matrix(settings.DPI/72, settings.DPI/72)  # Scale factor
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("ppm")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)
            
            doc.close()
            logger.info(f"Converted PDF to {len(images)} images using PyMuPDF")
            return images
            
        except ImportError:
            logger.error("Neither pdf2image nor PyMuPDF available. Please install one: pip install pdf2image OR pip install PyMuPDF")
            return []
        except Exception as e:
            logger.error(f"Failed to convert PDF to images with PyMuPDF: {e}")
            return []
    
    def _process_page(self, image, page_num: int) -> Dict[str, Any]:
        """
        Process a single page image
        
        Args:
            image: PIL Image object
            page_num: Page number
            
        Returns:
            Dictionary containing page results
        """
        import numpy as np
        
        image_array = np.array(image)
        
        regions = self._analyze_layout(image_array)
        
        processed_regions = []
        
        for region in regions:
            region_bbox = region.get('bbox')
            
            if self.table_extractor and self.table_extractor.can_handle(image_array, region_bbox):
                try:
                    result = self.table_extractor.extract(image_array, region_bbox)
                    if result.get('confidence', 0) > 0.5:
                        logger.info(f"Found table in region {region_bbox} with confidence {result.get('confidence')}")
                        processed_regions.append(result)
                        continue
                except Exception as e:
                    logger.warning(f"Table extraction failed for region {region_bbox}: {e}")
            
            try:
                result = self.text_extractor.extract(image_array, region_bbox)
                if result.get('content', '').strip():
                    logger.info(f"Found text in region {region_bbox} with confidence {result.get('confidence')}")
                    processed_regions.append(result)
            except Exception as e:
                logger.warning(f"Text extraction failed for region {region_bbox}: {e}")
        
        return {
            'page_number': page_num,
            'regions': processed_regions,
            'region_count': len(processed_regions)
        }
    
    def _analyze_layout(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Advanced layout analysis to identify content regions
        
        Args:
            image: Image as numpy array
            
        Returns:
            List of regions with bounding boxes
        """
        height, width = image.shape[:2]
        
        regions = []
        
        grid_size = 4
        cell_height = height // grid_size
        cell_width = width // grid_size
        
        for row in range(grid_size):
            for col in range(grid_size):
                y1 = row * cell_height
                y2 = min((row + 1) * cell_height, height)
                x1 = col * cell_width
                x2 = min((col + 1) * cell_width, width)
                
                cell = image[y1:y2, x1:x2]
                
                if cell.size > 0:
                    if len(cell.shape) == 3:
                        gray_cell = np.mean(cell, axis=2)
                    else:
                        gray_cell = cell
                    
                    content_ratio = np.sum(gray_cell < 240) / gray_cell.size
                    
                    if content_ratio > 0.05:
                        regions.append({
                            'bbox': (x1, y1, x2, y2),
                            'type': 'text',
                            'confidence': content_ratio,
                            'content_density': content_ratio
                        })
        
        if not regions:
            regions = [{
                'bbox': (0, 0, width, height),
                'type': 'text',
                'confidence': 1.0,
                'content_density': 1.0
            }]
        
        logger.info(f"Layout analysis found {len(regions)} content regions")
        return regions
    
    def save_results(self, results: Dict[str, Any], output_path: Path, output_format: str = 'json'):
        """Save processing results to file"""
        if output_format == 'text':
            text_content = self.text_formatter.format_results(results)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
        
        elif output_format == 'rag':
            text_content = self.text_formatter.format_for_rag(results)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
        
        else:
            import json
            serializable_results = self._make_serializable(results)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {output_path} in {output_format} format")
    
    def _make_serializable(self, obj):
        """Convert object to JSON-serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        else:
            return str(obj)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Process documents with advanced OCR")
    parser.add_argument("input", type=Path, help="Input PDF file")
    parser.add_argument("-o", "--output", type=Path, help="Output file")
    parser.add_argument("-f", "--format", choices=['json', 'text', 'rag'], default='json', 
                       help="Output format: json (default), text (readable), or rag (optimized for RAG systems)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        return 1
    
    if args.input.suffix.lower() != '.pdf':
        logger.error("Only PDF files are supported")
        return 1
    
    # Set default output path based on format
    if not args.output:
        if args.format == 'json':
            args.output = args.input.with_suffix('.json')
        else:
            args.output = args.input.with_suffix('.txt')
    
    try:
        # Process document
        processor = DocumentProcessor()
        results = processor.process_pdf(args.input)
        
        # Save results
        processor.save_results(results, args.output, args.format)
        
        # Print summary
        summary = results['summary']
        print(f"\nProcessing Summary:")
        print(f"  Pages processed: {summary['total_pages']}")
        print(f"  Text regions: {summary['text_regions']}")
        print(f"  Tables found: {summary['tables']}")
        print(f"  Results saved to: {args.output}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return 1

if __name__ == "__main__":
    
    
    sys.exit(main())