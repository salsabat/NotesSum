import argparse
import logging
import os
from pathlib import Path
import sys
from typing import List, Dict, Any
import numpy as np

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import settings
from src.extractors.text_extractor import TextExtractor
from src.extractors.table_extractor import TableExtractor
from src.processors.text_formatter import TextFormatter

from embedder import Embedder
from pinecone import PineconeClient

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
        logger.info("Document processor initialized")

    def process_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Process a PDF file and extract all content
        """
        logger.info(f"Processing PDF: {pdf_path}")
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
                rtype = region.get('type', 'unknown')
                if rtype in results['summary']:
                    results['summary'][rtype] += 1
        logger.info(f"Processing complete. Found {results['summary']}")
        return results


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

    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        return 1
    if args.input.suffix.lower() != '.pdf':
        logger.error("Only PDF files are supported")
        return 1
    
    if not args.output:
        args.output = args.input.with_suffix('.json') if args.format == 'json' else args.input.with_suffix('.txt')

    try:
        #process document
        processor = DocumentProcessor()
        results = processor.process_pdf(args.input)

        #initialize pinecone & embedder
        pc_client = PineconeClient(
            api_key=os.getenv("PINECONE_API_KEY"),
            environment=os.getenv("PINECONE_ENVIRONMENT")
        )
        pc_index = pc_client.Index(os.getenv("PINECONE_INDEX_NAME"))
        embedder = Embedder(pcdb_instance=pc_index)

        #gather all text regions for embedding
        all_text_chunks: List[str] = []
        for page in results['pages']:
            for region in page['regions']:
                if region.get('type') == 'Text':
                    content = region.get('content', '').strip()
                    if content:
                        all_text_chunks.append(content)
        document_text = "\n".join(all_text_chunks)

        #embed and upsert to Pinecone
        logger.info("Embedding and uploading document text to Pinecone...")
        pinecone_vectors = embedder.embed_document(document_text, category=args.input.stem)
        pc_index.upsert(pinecone_vectors)

        #save results locally
        processor.save_results(results, args.output, args.format)

        #print summary
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
