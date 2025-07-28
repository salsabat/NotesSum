import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import cv2
from bs4 import BeautifulSoup
import pandas as pd

try:
    from paddleocr import PPStructure
    PADDLE_STRUCTURE_AVAILABLE = True
except ImportError:
    PADDLE_STRUCTURE_AVAILABLE = False

from .base import BaseExtractor
from ..config import settings

class TableExtractor(BaseExtractor):
    """Extract table data using PaddleOCR PP-Structure"""
    
    def __init__(self, confidence_threshold: float = 0.8):
        super().__init__(confidence_threshold)
        
        if PADDLE_STRUCTURE_AVAILABLE:
            try:
                self.table_engine = PPStructure(
                    table=True,
                    ocr=True,
                    show_log=False,
                    recovery=True,  # Enables table structure recovery
                    lang=settings.PADDLE_OCR_LANG
                )
                self.engine_available = True
                self.logger.info("PaddleOCR PP-Structure initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize PP-Structure: {e}")
                self.engine_available = False
        else:
            self.engine_available = False
            self.logger.warning("PaddleOCR PP-Structure not available")
    
    def can_handle(self, image: np.ndarray, region_bbox: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """
        Determine if this region contains a table
        
        Args:
            image: Input image
            region_bbox: Optional bounding box to check
            
        Returns:
            True if region likely contains a table
        """
        if not self.engine_available:
            return False
        
        processed_image = self.preprocess_image(image, region_bbox)
        return self._detect_table_structure(processed_image)
    
    def extract(self, image: np.ndarray, region_bbox: Optional[Tuple[int, int, int, int]] = None) -> Dict[str, Any]:
        """
        Extract table structure and data
        
        Args:
            image: Input image as numpy array
            region_bbox: Optional bounding box to extract from
            
        Returns:
            Dictionary containing table data and structure
        """
        if not self.engine_available:
            return {
                'type': 'table',
                'error': 'Table extraction engine not available',
                'confidence': 0.0
            }
        
        # Preprocess image
        processed_image = self.preprocess_image(image, region_bbox)
        
        # Enhance image for better table detection
        enhanced_image = self.enhance_image_quality(processed_image)
        
        try:
            # Extract table using PP-Structure
            results = self.table_engine(enhanced_image)
            
            tables = []
            for region in results:
                if region.get('type') == 'table':
                    table_data = self._process_table_region(region)
                    if table_data:
                        tables.append(table_data)
            
            if tables:
                # Return the largest/most confident table
                best_table = max(tables, key=lambda x: x.get('confidence', 0))
                return best_table
            else:
                # Fallback: try basic table detection
                return self._fallback_table_extraction(enhanced_image)
        
        except Exception as e:
            self.logger.error(f"Table extraction failed: {e}")
            return {
                'type': 'table',
                'error': str(e),
                'confidence': 0.0
            }
    
    def _process_table_region(self, region: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a table region from PP-Structure results"""
        try:
            # Get table HTML if available
            table_html = region.get('res', {}).get('html', '')
            
            if table_html:
                # Parse HTML table
                table_data = self._parse_html_table(table_html)
                
                return {
                    'type': 'table',
                    'data': table_data,
                    'html': table_html,
                    'bbox': region.get('bbox', []),
                    'confidence': self._calculate_table_confidence(table_data),
                    'rows': len(table_data),
                    'columns': len(table_data[0]) if table_data else 0,
                    'extractor': 'PP-Structure'
                }
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to process table region: {e}")
            return None
    
    def _parse_html_table(self, html_table: str) -> List[List[str]]:
        """
        Parse HTML table into structured data
        
        Args:
            html_table: HTML table string
            
        Returns:
            2D list representing table data
        """
        try:
            soup = BeautifulSoup(html_table, 'html.parser')
            table = soup.find('table')
            
            if not table:
                return []
            
            rows = []
            for tr in table.find_all('tr'):
                row = []
                for cell in tr.find_all(['td', 'th']):
                    # Handle colspan and rowspan
                    cell_text = cell.get_text(strip=True)
                    colspan = int(cell.get('colspan', 1))
                    
                    # Add cell content
                    row.append(cell_text)
                    
                    # Add empty cells for colspan
                    for _ in range(colspan - 1):
                        row.append('')
                
                if row:  # Only add non-empty rows
                    rows.append(row)
            
            # Normalize row lengths
            if rows:
                max_cols = max(len(row) for row in rows)
                for row in rows:
                    while len(row) < max_cols:
                        row.append('')
            
            return rows
            
        except Exception as e:
            self.logger.warning(f"Failed to parse HTML table: {e}")
            return []
    
    def _detect_table_structure(self, image: np.ndarray) -> bool:
        """
        Detect if image contains table structure using line detection
        
        Args:
            image: Input image
            
        Returns:
            True if table structure detected
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # Apply threshold
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Detect horizontal lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel)
            
            # Detect vertical lines
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
            vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel)
            
            # Count line pixels
            h_lines_count = np.sum(horizontal_lines > 0)
            v_lines_count = np.sum(vertical_lines > 0)
            
            # Check if we have both horizontal and vertical lines
            return (h_lines_count > settings.TABLE_LINE_THRESHOLD and 
                    v_lines_count > settings.TABLE_LINE_THRESHOLD)
            
        except Exception as e:
            self.logger.warning(f"Table structure detection failed: {e}")
            return False
    
    def _fallback_table_extraction(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Fallback table extraction using basic OCR and structure detection
        
        Args:
            image: Input image
            
        Returns:
            Table extraction result
        """
        try:
            # Use basic OCR to get text regions
            from .text_extractor import TextExtractor
            text_extractor = TextExtractor()
            
            text_result = text_extractor.extract(image)
            word_boxes = text_result.get('word_boxes', [])
            
            if not word_boxes:
                return {
                    'type': 'table',
                    'error': 'No text found for table extraction',
                    'confidence': 0.0
                }
            
            # Group words into table cells based on position
            table_data = self._group_words_into_table(word_boxes, image.shape)
            
            if table_data and len(table_data) > 1:  # At least 2 rows
                return {
                    'type': 'table',
                    'data': table_data,
                    'bbox': [0, 0, image.shape[1], image.shape[0]],
                    'confidence': 0.6,  # Lower confidence for fallback method
                    'rows': len(table_data),
                    'columns': len(table_data[0]) if table_data else 0,
                    'extractor': 'Fallback'
                }
            
            return {
                'type': 'table',
                'error': 'Could not detect table structure',
                'confidence': 0.0
            }
            
        except Exception as e:
            self.logger.error(f"Fallback table extraction failed: {e}")
            return {
                'type': 'table',
                'error': str(e),
                'confidence': 0.0
            }
    
    def _group_words_into_table(self, word_boxes: List[Dict[str, Any]], image_shape: Tuple[int, ...]) -> List[List[str]]:
        """
        Group word boxes into table structure based on spatial arrangement
        
        Args:
            word_boxes: List of word boxes with positions
            image_shape: Shape of the image
            
        Returns:
            2D list representing table data
        """
        if not word_boxes:
            return []
        
        # Sort words by vertical position
        sorted_words = sorted(word_boxes, key=lambda x: self._get_bbox_center_y(x['bbox']))
        
        # Group words into rows based on Y position
        rows = []
        current_row = []
        current_y = None
        row_height_threshold = 30  # Pixels
        
        for word in sorted_words:
            y_center = self._get_bbox_center_y(word['bbox'])
            
            if current_y is None:
                current_y = y_center
                current_row = [word]
            elif abs(y_center - current_y) <= row_height_threshold:
                current_row.append(word)
            else:
                # Process current row
                if current_row:
                    row_data = self._process_table_row(current_row)
                    if row_data:
                        rows.append(row_data)
                
                # Start new row
                current_row = [word]
                current_y = y_center
        
        # Process last row
        if current_row:
            row_data = self._process_table_row(current_row)
            if row_data:
                rows.append(row_data)
        
        return rows
    
    def _process_table_row(self, row_words: List[Dict[str, Any]]) -> List[str]:
        """
        Process words in a table row, sorting by X position
        
        Args:
            row_words: List of words in the same row
            
        Returns:
            List of cell contents
        """
        # Sort by X position
        sorted_words = sorted(row_words, key=lambda x: self._get_bbox_center_x(x['bbox']))
        
        # Extract text content
        return [word['text'] for word in sorted_words]
    
    def _get_bbox_center_x(self, bbox) -> float:
        """Get center X coordinate of bounding box"""
        if isinstance(bbox[0], (list, tuple)):
            return sum(point[0] for point in bbox) / len(bbox)
        else:
            return (bbox[0] + bbox[2]) / 2
    
    def _get_bbox_center_y(self, bbox) -> float:
        """Get center Y coordinate of bounding box"""
        if isinstance(bbox[0], (list, tuple)):
            return sum(point[1] for point in bbox) / len(bbox)
        else:
            return (bbox[1] + bbox[3]) / 2
    
    def _calculate_table_confidence(self, table_data: List[List[str]]) -> float:
        """
        Calculate confidence score for extracted table
        
        Args:
            table_data: 2D list of table data
            
        Returns:
            Confidence score between 0 and 1
        """
        if not table_data:
            return 0.0
        
        # Factors that increase confidence:
        # 1. Regular structure (consistent column count)
        # 2. Non-empty cells
        # 3. Reasonable size
        
        rows = len(table_data)
        if rows == 0:
            return 0.0
        
        # Check column consistency
        col_counts = [len(row) for row in table_data]
        avg_cols = sum(col_counts) / len(col_counts)
        col_variance = sum((count - avg_cols) ** 2 for count in col_counts) / len(col_counts)
        
        structure_score = max(0, 1 - (col_variance / (avg_cols + 1)))
        
        # Check content density
        total_cells = sum(col_counts)
        non_empty_cells = sum(1 for row in table_data for cell in row if cell.strip())
        content_score = non_empty_cells / total_cells if total_cells > 0 else 0
        
        # Size score (prefer tables with reasonable dimensions)
        size_score = min(1.0, (rows * avg_cols) / 20)  # Normalize to reasonable table size
        
        # Combine scores
        confidence = (structure_score * 0.4 + content_score * 0.4 + size_score * 0.2)
        
        return min(1.0, confidence)
    
    def calculate_confidence(self, extracted_data: Dict[str, Any]) -> float:
        """Calculate confidence score for extracted table"""
        return extracted_data.get('confidence', 0.0)