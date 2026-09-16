"""
Image quality assessment for CauseListOCR
"""

import cv2
import numpy as np
from typing import Tuple, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ImageQualityAssessor:
    """Assess image quality metrics."""
    
    @staticmethod
    def assess_sharpness(image: np.ndarray) -> float:
        """Calculate image sharpness using Laplacian variance.
        
        Args:
            image: Input image
            
        Returns:
            Sharpness score (higher = sharper)
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = np.var(laplacian)
        return float(variance)
    
    @staticmethod
    def assess_contrast(image: np.ndarray) -> float:
        """Calculate image contrast using standard deviation.
        
        Args:
            image: Input image
            
        Returns:
            Contrast score (higher = higher contrast)
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        return float(np.std(gray))
    
    @staticmethod
    def assess_brightness(image: np.ndarray) -> float:
        """Calculate average brightness.
        
        Args:
            image: Input image
            
        Returns:
            Brightness score (0-255)
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        return float(np.mean(gray))
    
    @staticmethod
    def assess_noise(image: np.ndarray) -> float:
        """Estimate noise level using Laplacian.
        
        Args:
            image: Input image
            
        Returns:
            Noise score (lower = less noise)
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Use high-pass filter to estimate noise
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        # Normalize to 0-1 range
        noise = np.mean(np.abs(laplacian)) / 255.0
        return float(noise)
    
    @staticmethod
    def assess_resolution(image: np.ndarray, dpi: int = 96) -> Tuple[float, float]:
        """Estimate image resolution quality.
        
        Args:
            image: Input image
            dpi: Assumed DPI (default 96)
            
        Returns:
            (height_inches, width_inches)
        """
        height, width = image.shape[:2]
        return (height / dpi, width / dpi)
    
    @classmethod
    def full_assessment(cls, image: np.ndarray) -> Dict[str, float]:
        """Perform comprehensive quality assessment.
        
        Args:
            image: Input image
            
        Returns:
            Dictionary of quality metrics
        """
        return {
            "sharpness": cls.assess_sharpness(image),
            "contrast": cls.assess_contrast(image),
            "brightness": cls.assess_brightness(image),
            "noise": cls.assess_noise(image),
        }
    
    @staticmethod
    def quality_score(metrics: Dict[str, float]) -> float:
        """Calculate weighted quality score.
        
        Args:
            metrics: Quality metrics from full_assessment
            
        Returns:
            Overall quality score (0-100)
        """
        # Normalize metrics
        sharpness_norm = min(metrics["sharpness"] / 100.0, 1.0)  # Assume 100 is good
        contrast_norm = min(metrics["contrast"] / 50.0, 1.0)      # Assume 50 is good
        noise_norm = max(1.0 - metrics["noise"] * 2, 0.0)        # Lower is better
        brightness_norm = min(metrics["brightness"] / 200.0, 1.0) # 100-200 is good range
        
        # Weighted average
        score = (
            sharpness_norm * 0.4 +
            contrast_norm * 0.3 +
            noise_norm * 0.2 +
            brightness_norm * 0.1
        )
        
        return float(score * 100)
