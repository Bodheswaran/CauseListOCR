"""
OCR Engine orchestration for CauseListOCR
Coordinates primary and secondary OCR with confidence scoring
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class OCRTextRegion:
    """Single text region detected by OCR."""
    text: str
    confidence: float  # 0.0-1.0
    bounding_box: List[Tuple[float, float]]  # List of (x, y) points
    engine: str  # "paddleocr", "tesseract", etc.


@dataclass
class OCRResult:
    """Complete OCR result from an image."""
    regions: List[OCRTextRegion]
    raw_text: str  # Concatenated text
    overall_confidence: float
    preprocessing_mode: str
    processing_time_seconds: float


class OCREngine:
    """Main OCR orchestration engine."""
    
    def __init__(self, use_paddle: bool = True, use_secondary: bool = False):
        """Initialize OCR engine.
        
        Args:
            use_paddle: Use PaddleOCR as primary engine
            use_secondary: Use secondary OCR for verification
        """
        self.use_paddle = use_paddle
        self.use_secondary = use_secondary
        self.paddle_ocr = None
        self.secondary_ocr = None
        
        if self.use_paddle:
            self._init_paddle_ocr()
    
    def _init_paddle_ocr(self):
        """Initialize PaddleOCR engine."""
        try:
            from app.ocr.primary_ocr import PaddleOCREngine
            self.paddle_ocr = PaddleOCREngine()
            logger.info("PaddleOCR engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            self.paddle_ocr = None
    
    def _init_secondary_ocr(self):
        """Initialize secondary OCR engine (future: Tesseract)."""
        # Future: Add Tesseract or other secondary OCR
        pass
    
    def extract_text(self, image: np.ndarray, preprocessing_mode: str = "auto") -> Optional[OCRResult]:
        """Extract text from image using primary OCR.
        
        Args:
            image: Input image as numpy array
            preprocessing_mode: Preprocessing mode used
            
        Returns:
            OCRResult or None if failed
        """
        if self.paddle_ocr is None:
            logger.error("No OCR engine available")
            return None
        
        try:
            result = self.paddle_ocr.extract_text(image)
            if result:
                result.preprocessing_mode = preprocessing_mode
            return result
        except Exception as e:
            logger.error(f"Error during OCR extraction: {e}")
            return None
    
    def extract_text_with_verification(self, image: np.ndarray) -> Optional[OCRResult]:
        """Extract text with secondary verification if enabled.
        
        Args:
            image: Input image
            
        Returns:
            OCRResult with enhanced confidence
        """
        if not self.use_secondary or self.secondary_ocr is None:
            return self.extract_text(image)
        
        try:
            primary_result = self.extract_text(image)
            if primary_result is None:
                return None
            
            # Get secondary result
            secondary_result = self.secondary_ocr.extract_text(image)
            if secondary_result is None:
                return primary_result
            
            # Merge results and enhance confidence
            return self._merge_ocr_results(primary_result, secondary_result)
        except Exception as e:
            logger.error(f"Error during OCR verification: {e}")
            return self.extract_text(image)
    
    def _merge_ocr_results(self, primary: OCRResult, secondary: OCRResult) -> OCRResult:
        """Merge primary and secondary OCR results.
        
        Args:
            primary: Primary OCR result
            secondary: Secondary OCR result
            
        Returns:
            Merged OCR result
        """
        # Simple merge: average confidence if texts match
        merged_regions = []
        
        for p_region in primary.regions:
            # Find matching region in secondary
            match_found = False
            for s_region in secondary.regions:
                if self._regions_match(p_region, s_region):
                    # Average confidence
                    avg_confidence = (p_region.confidence + s_region.confidence) / 2.0
                    merged_regions.append(
                        OCRTextRegion(
                            text=p_region.text,
                            confidence=avg_confidence,
                            bounding_box=p_region.bounding_box,
                            engine="paddle+secondary"
                        )
                    )
                    match_found = True
                    break
            
            if not match_found:
                # Keep primary result
                merged_regions.append(p_region)
        
        # Add secondary-only regions
        for s_region in secondary.regions:
            if not any(self._regions_match(s_region, p) for p in primary.regions):
                merged_regions.append(s_region)
        
        # Calculate overall confidence
        overall_conf = np.mean([r.confidence for r in merged_regions]) if merged_regions else 0.0
        
        return OCRResult(
            regions=merged_regions,
            raw_text=primary.raw_text,
            overall_confidence=float(overall_conf),
            preprocessing_mode=primary.preprocessing_mode,
            processing_time_seconds=primary.processing_time_seconds
        )
    
    @staticmethod
    def _regions_match(region1: OCRTextRegion, region2: OCRTextRegion, threshold: float = 0.7) -> bool:
        """Check if two regions match (similar text and position).
        
        Args:
            region1: First region
            region2: Second region
            threshold: Similarity threshold (0.0-1.0)
            
        Returns:
            True if regions match
        """
        # Simple: check if text is very similar and bounding boxes overlap
        # Future: Use Levenshtein distance and IoU for better matching
        return region1.text.lower() == region2.text.lower()
