"""
Image preprocessing pipeline for CauseListOCR
Multiple enhancement modes with quality metrics
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PreprocessMode(Enum):
    """Available preprocessing modes."""
    ORIGINAL = "original"
    UPSCALE_2X = "upscale_2x"
    UPSCALE_3X = "upscale_3x"
    GRAYSCALE = "grayscale"
    CONTRAST = "contrast"
    SHARP = "sharp"
    DENOISE = "denoise"
    ADAPTIVE_THRESHOLD = "adaptive_threshold"
    OTSU_THRESHOLD = "otsu_threshold"
    BINARY_THRESHOLD = "binary_threshold"


class ImagePreprocessor:
    """Production-grade image preprocessing for OCR."""
    
    def __init__(self, log_processing: bool = True):
        """Initialize preprocessor.
        
        Args:
            log_processing: Log preprocessing operations
        """
        self.log_processing = log_processing
        self.processing_log: Dict[str, any] = {}
    
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """Load image from file.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Loaded image array or None if failed
        """
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return None
            logger.info(f"Loaded image: {image_path} ({image.shape})")
            return image
        except Exception as e:
            logger.exception(f"Error loading image {image_path}: {e}")
            return None
    
    def preprocess_original(self, image: np.ndarray) -> np.ndarray:
        """Return original image.
        
        Args:
            image: Input image
            
        Returns:
            Original image
        """
        return image.copy()
    
    def preprocess_upscale_2x(self, image: np.ndarray) -> np.ndarray:
        """Upscale image 2x using cubic interpolation.
        
        Args:
            image: Input image
            
        Returns:
            Upscaled image
        """
        height, width = image.shape[:2]
        return cv2.resize(image, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
    
    def preprocess_upscale_3x(self, image: np.ndarray) -> np.ndarray:
        """Upscale image 3x using cubic interpolation.
        
        Args:
            image: Input image
            
        Returns:
            Upscaled image
        """
        height, width = image.shape[:2]
        return cv2.resize(image, (width * 3, height * 3), interpolation=cv2.INTER_CUBIC)
    
    def preprocess_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convert to grayscale.
        
        Args:
            image: Input image (BGR)
            
        Returns:
            Grayscale image
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Convert back to 3-channel for consistency
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    
    def preprocess_contrast(self, image: np.ndarray, alpha: float = 1.5, beta: float = 30) -> np.ndarray:
        """Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization).
        
        Args:
            image: Input image (BGR)
            alpha: Contrast control (1.0-3.0)
            beta: Brightness control
            
        Returns:
            Contrast-enhanced image
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge and convert back
        lab = cv2.merge([l, a, b])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    def preprocess_sharp(self, image: np.ndarray, strength: float = 1.5) -> np.ndarray:
        """Sharpen image using unsharp mask.
        
        Args:
            image: Input image
            strength: Sharpening strength (1.0-3.0)
            
        Returns:
            Sharpened image
        """
        gaussian = cv2.GaussianBlur(image, (0, 0), 1.0)
        sharpened = cv2.addWeighted(image, 1.0 + strength, gaussian, -strength, 0)
        return np.clip(sharpened, 0, 255).astype(np.uint8)
    
    def preprocess_denoise(self, image: np.ndarray) -> np.ndarray:
        """Denoise using bilateral filter.
        
        Args:
            image: Input image
            
        Returns:
            Denoised image
        """
        return cv2.bilateralFilter(image, 9, 75, 75)
    
    def preprocess_adaptive_threshold(self, image: np.ndarray, block_size: int = 11) -> np.ndarray:
        """Apply adaptive thresholding.
        
        Args:
            image: Input image
            block_size: Neighborhood block size (must be odd)
            
        Returns:
            Binary image
        """
        # Ensure block_size is odd
        if block_size % 2 == 0:
            block_size += 1
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            block_size,
            2
        )
        return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    
    def preprocess_otsu_threshold(self, image: np.ndarray) -> np.ndarray:
        """Apply Otsu's automatic thresholding.
        
        Args:
            image: Input image
            
        Returns:
            Binary image
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    
    def preprocess_binary_threshold(self, image: np.ndarray, threshold: int = 127) -> np.ndarray:
        """Apply binary thresholding.
        
        Args:
            image: Input image
            threshold: Threshold value (0-255)
            
        Returns:
            Binary image
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
        return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    
    def preprocess(self, image: np.ndarray, mode: PreprocessMode) -> np.ndarray:
        """Apply preprocessing based on mode.
        
        Args:
            image: Input image
            mode: Preprocessing mode
            
        Returns:
            Preprocessed image
        """
        if mode == PreprocessMode.ORIGINAL:
            return self.preprocess_original(image)
        elif mode == PreprocessMode.UPSCALE_2X:
            return self.preprocess_upscale_2x(image)
        elif mode == PreprocessMode.UPSCALE_3X:
            return self.preprocess_upscale_3x(image)
        elif mode == PreprocessMode.GRAYSCALE:
            return self.preprocess_grayscale(image)
        elif mode == PreprocessMode.CONTRAST:
            return self.preprocess_contrast(image)
        elif mode == PreprocessMode.SHARP:
            return self.preprocess_sharp(image)
        elif mode == PreprocessMode.DENOISE:
            return self.preprocess_denoise(image)
        elif mode == PreprocessMode.ADAPTIVE_THRESHOLD:
            return self.preprocess_adaptive_threshold(image)
        elif mode == PreprocessMode.OTSU_THRESHOLD:
            return self.preprocess_otsu_threshold(image)
        elif mode == PreprocessMode.BINARY_THRESHOLD:
            return self.preprocess_binary_threshold(image)
        else:
            logger.warning(f"Unknown preprocessing mode: {mode}, returning original")
            return image.copy()
    
    def preprocess_all_modes(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        """Generate all preprocessing modes for comparison.
        
        Args:
            image: Input image
            
        Returns:
            Dictionary of {mode_name: preprocessed_image}
        """
        results = {}
        for mode in PreprocessMode:
            try:
                results[mode.value] = self.preprocess(image, mode)
                if self.log_processing:
                    logger.debug(f"Generated preprocessing mode: {mode.value}")
            except Exception as e:
                logger.warning(f"Failed to generate {mode.value}: {e}")
        return results
