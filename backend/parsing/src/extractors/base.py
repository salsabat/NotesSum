from abc import ABC, abstractmethod
from typing import Dict, Any, List
import numpy as np

class BaseExtractor(ABC):
    """Base class for all extractors"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
    
    @abstractmethod
    def extract(self, image: np.ndarray, **kwargs) -> List[Dict[str, Any]]:
        """
        Extract content from an image
        
        Args:
            image: Input image as numpy array
            **kwargs: Additional arguments
            
        Returns:
            List of extracted regions with metadata
        """
        pass
    
    def get_name(self) -> str:
        """Get the name of this extractor"""
        return self.__class__.__name__
    
    def get_config(self) -> Dict[str, Any]:
        """Get the configuration for this extractor"""
        return self.config.copy() 