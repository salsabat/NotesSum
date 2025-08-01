import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import paddleocr
import easyocr
import cv2
from PIL import Image
import logging

from .base import BaseExtractor
from ..config import settings

class TextExtractor(BaseExtractor):
    """Extract plain text using PaddleOCR with EasyOCR fallback"""
    
    def __init__(self, confidence_threshold: float = 0.8):
        super().__init__({'confidence_threshold': confidence_threshold})
        self.confidence_threshold = confidence_threshold
        self.logger = logging.getLogger(__name__)
        
        # Initialize PaddleOCR
        try:
            self.paddle_ocr = paddleocr.PaddleOCR(
                use_angle_cls=True,
                lang=settings.PADDLE_OCR_LANG,
                show_log=False
            )
            self.paddle_available = True
            self.logger.info("PaddleOCR initialized successfully")
        except Exception as e:
            self.logger.warning(f"Failed to initialize PaddleOCR: {e}")
            self.paddle_available = False
        
        # Initialize EasyOCR as fallback
        try:
            self.easy_ocr = easyocr.Reader(['en'], gpu=False)  # CPU mode for compatibility
            self.easy_available = True
            self.logger.info("EasyOCR initialized successfully")
        except Exception as e:
            self.logger.warning(f"Failed to initialize EasyOCR: {e}")
            self.easy_available = False
        
        if not self.paddle_available and not self.easy_available:
            raise RuntimeError("Neither PaddleOCR nor EasyOCR could be initialized")
    
    def can_handle(self, image: np.ndarray, region_bbox: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """
        Text extractor can handle any region, but with lower priority than specialized extractors
        """
        return True
    
    def extract(self, image: np.ndarray, region_bbox: Optional[Tuple[int, int, int, int]] = None) -> Dict[str, Any]:
        """
        Extract text from image region
        
        Args:
            image: Input image as numpy array
            region_bbox: Optional bounding box to extract from
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        # Preprocess image
        processed_image = self.preprocess_image(image, region_bbox)
        
        # Enhance image quality
        enhanced_image = self.enhance_image_quality(processed_image)
        
        # Try PaddleOCR first
        if self.paddle_available:
            try:
                result = self._extract_with_paddle(enhanced_image)
                if result['confidence'] >= self.confidence_threshold:
                    result['extractor'] = 'PaddleOCR'
                    return result
            except Exception as e:
                self.logger.warning(f"PaddleOCR extraction failed: {e}")
        
        # Fallback to EasyOCR
        if self.easy_available:
            try:
                result = self._extract_with_easy(enhanced_image)
                result['extractor'] = 'EasyOCR'
                return result
            except Exception as e:
                self.logger.error(f"EasyOCR extraction failed: {e}")
        
        # Return empty result if all methods fail
        return {
            'type': 'text',
            'content': '',
            'confidence': 0.0,
            'word_boxes': [],
            'extractor': 'none',
            'error': 'All OCR methods failed'
        }
    
    def _extract_with_paddle(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract text using PaddleOCR"""
        results = self.paddle_ocr.ocr(image, cls=True)
        
        if not results or not results[0]:
            return {
                'type': 'text',
                'content': '',
                'confidence': 0.0,
                'word_boxes': []
            }
        
        text_blocks = []
        word_boxes = []
        total_confidence = 0.0
        
        for line in results[0]:
            if line:
                bbox, (text, confidence) = line
                
                if confidence >= self.confidence_threshold:
                    text_blocks.append(text)
                    word_boxes.append({
                        'text': text,
                        'bbox': bbox,
                        'confidence': confidence
                    })
                    total_confidence += confidence
        
        # Calculate average confidence
        avg_confidence = total_confidence / len(word_boxes) if word_boxes else 0.0
        
        # Join text blocks with spaces, preserving line breaks
        content = self._reconstruct_text_layout(word_boxes)
        
        return {
            'type': 'text',
            'content': content,
            'confidence': avg_confidence,
            'word_boxes': word_boxes,
            'word_count': len(text_blocks),
            'line_count': len(results[0]) if results[0] else 0
        }
    
    def _extract_with_easy(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract text using EasyOCR"""
        results = self.easy_ocr.readtext(image)
        
        if not results:
            return {
                'type': 'text',
                'content': '',
                'confidence': 0.0,
                'word_boxes': []
            }
        
        text_blocks = []
        word_boxes = []
        total_confidence = 0.0
        
        for bbox, text, confidence in results:
            if confidence >= self.confidence_threshold:
                text_blocks.append(text)
                word_boxes.append({
                    'text': text,
                    'bbox': bbox,
                    'confidence': confidence
                })
                total_confidence += confidence
        
        # Calculate average confidence
        avg_confidence = total_confidence / len(word_boxes) if word_boxes else 0.0
        
        # Reconstruct text layout
        content = self._reconstruct_text_layout(word_boxes)
        
        return {
            'type': 'text',
            'content': content,
            'confidence': avg_confidence,
            'word_boxes': word_boxes,
            'word_count': len(text_blocks),
            'line_count': self._estimate_line_count(word_boxes)
        }
    
    def _reconstruct_text_layout(self, word_boxes: List[Dict[str, Any]]) -> str:
        """
        Reconstruct text layout by sorting words by position
        
        Args:
            word_boxes: List of word boxes with text and bbox
            
        Returns:
            Reconstructed text with proper spacing and line breaks
        """
        if not word_boxes:
            return ""
        
        # Sort by vertical position first, then horizontal
        sorted_boxes = sorted(word_boxes, key=lambda x: (
            self._get_bbox_center_y(x['bbox']),
            self._get_bbox_center_x(x['bbox'])
        ))
        
        lines = []
        current_line = []
        current_y = None
        line_height_threshold = 20  # Pixels
        
        for box in sorted_boxes:
            y_center = self._get_bbox_center_y(box['bbox'])
            
            if current_y is None:
                current_y = y_center
                current_line = [box['text']]
            elif abs(y_center - current_y) <= line_height_threshold:
                # Same line
                current_line.append(box['text'])
            else:
                # New line
                lines.append(' '.join(current_line))
                current_line = [box['text']]
                current_y = y_center
        
        # Add the last line
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
    
    def _get_bbox_center_x(self, bbox) -> float:
        """Get center X coordinate of bounding box"""
        if isinstance(bbox[0], (list, tuple)):
            # PaddleOCR format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            return sum(point[0] for point in bbox) / len(bbox)
        else:
            # EasyOCR format: [x1, y1, x2, y2] or similar
            return (bbox[0] + bbox[2]) / 2
    
    def _get_bbox_center_y(self, bbox) -> float:
        """Get center Y coordinate of bounding box"""
        if isinstance(bbox[0], (list, tuple)):
            # PaddleOCR format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            return sum(point[1] for point in bbox) / len(bbox)
        else:
            # EasyOCR format: [x1, y1, x2, y2] or similar
            return (bbox[1] + bbox[3]) / 2
    
    def _estimate_line_count(self, word_boxes: List[Dict[str, Any]]) -> int:
        """Estimate number of text lines"""
        if not word_boxes:
            return 0
        
        y_positions = [self._get_bbox_center_y(box['bbox']) for box in word_boxes]
        y_positions.sort()
        
        line_count = 1
        line_height_threshold = 20
        
        for i in range(1, len(y_positions)):
            if y_positions[i] - y_positions[i-1] > line_height_threshold:
                line_count += 1
        
        return line_count
    
    def calculate_confidence(self, extracted_data: Dict[str, Any]) -> float:
        """Calculate confidence score for extracted text"""
        if not extracted_data.get('word_boxes'):
            return 0.0
        
        return extracted_data.get('confidence', 0.0)
    
    def preprocess_image(self, image: np.ndarray, region_bbox: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """Preprocess image for OCR"""
        if region_bbox is not None:
            x1, y1, x2, y2 = region_bbox
            image = image[y1:y2, x1:x2]
        
        # Convert to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            # Already RGB
            pass
        elif len(image.shape) == 3 and image.shape[2] == 4:
            # RGBA to RGB
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        elif len(image.shape) == 2:
            # Grayscale to RGB
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        
        return image
    
    def enhance_image_quality(self, image: np.ndarray) -> np.ndarray:
        """Enhance image quality for better OCR results"""
        # Convert to grayscale for processing
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Apply slight Gaussian blur to reduce noise
        enhanced = cv2.GaussianBlur(enhanced, (1, 1), 0)
        
        # Convert back to RGB
        enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
        
        return enhanced_rgb