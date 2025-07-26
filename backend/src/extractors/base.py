from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from PIL import Image
import cv2
import logging

logger = logging.getLogger(__name__)

class BaseExtractor(ABC):
    """Base class for all content extractors"""
    
    def __init__(self, confidence_threshold: float = 0.8):
        self.confidence_threshold = confidence_threshold
        self.logger = logger
    
    @abstractmethod
    def extract(self, image: np.ndarray, region_bbox: Optional[Tuple[int, int, int, int]] = None) -> Dict[str, Any]:
        """
        Extract content from an image region
        
        Args:
            image: Input image as numpy array
            region_bbox: Optional bounding box (x1, y1, x2, y2) to extract from
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        pass
    
    @abstractmethod
    def can_handle(self, image: np.ndarray, region_bbox: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """
        Determine if this extractor can handle the given image region
        
        Args:
            image: Input image as numpy array
            region_bbox: Optional bounding box to check
            
        Returns:
            True if this extractor can handle the content
        """
        pass
    
    def preprocess_image(self, image: np.ndarray, region_bbox: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """
        Preprocess image for extraction
        
        Args:
            image: Input image
            region_bbox: Optional region to extract
            
        Returns:
            Preprocessed image
        """
        if region_bbox:
            x1, y1, x2, y2 = region_bbox
            image = image[y1:y2, x1:x2]
        
        # Basic preprocessing
        if len(image.shape) == 3:
            # Ensure RGB format
            if image.shape[2] == 4:  # RGBA
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
            elif image.shape[2] == 3 and image.dtype == np.uint8:
                # Assume BGR, convert to RGB
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        return image
    
    def enhance_image_quality(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image quality for better OCR results
        
        Args:
            image: Input image
            
        Returns:
            Enhanced image
        """
        # Convert to grayscale for processing
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(enhanced)
        
        # Convert back to RGB if original was color
        if len(image.shape) == 3:
            enhanced_rgb = cv2.cvtColor(denoised, cv2.COLOR_GRAY2RGB)
            return enhanced_rgb
        
        return denoised
    
    def get_text_regions(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Get text regions from image using basic contour detection
        
        Args:
            image: Input image
            
        Returns:
            List of text regions with bounding boxes
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Apply threshold
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter small regions
            if w > 10 and h > 10:
                regions.append({
                    'bbox': (x, y, x + w, y + h),
                    'area': w * h,
                    'aspect_ratio': w / h
                })
        
        # Sort by area (largest first)
        regions.sort(key=lambda x: x['area'], reverse=True)
        
        return regions
    
    def calculate_confidence(self, extracted_data: Dict[str, Any]) -> float:
        """
        Calculate confidence score for extracted data
        
        Args:
            extracted_data: Extracted content data
            
        Returns:
            Confidence score between 0 and 1
        """
        # Default implementation - subclasses should override
        return 0.5