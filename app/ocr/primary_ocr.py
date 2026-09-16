"""
PaddleOCR implementation for CauseListOCR
Python 3.14 compatible primary OCR engine
"""

import logging
import time
from typing import List, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)


class PaddleOCREngine:
    """PaddleOCR wrapper for text extraction."""
    
    def __init__(self, use_gpu: bool = False, lang: str = "en"):
        """Initialize PaddleOCR.
        
        Args:
            use_gpu: Use GPU (default False for compatibility)
            lang: Language code (default 'en' for English)
        """
        self.use_gpu = use_gpu
        self.lang = lang
        self.ocr = None
        
        try:
            from paddleocr import PaddleOCR
            from app.utils.paths import AppPaths
            
            # Ensure model directory exists
            AppPaths.ensure_dirs()
            model_dir = str(AppPaths.get_models_dir())
            
            logger.info(f"Initializing PaddleOCR (GPU={use_gpu}, lang={lang})")
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang=lang,
                use_gpu=use_gpu,
                model_storage_directory=model_dir,
                det_model_dir=f"{model_dir}/paddleocr/det",
                rec_model_dir=f"{model_dir}/paddleocr/rec",
                cls_model_dir=f"{model_dir}/paddleocr/cls"
            )
            logger.info("PaddleOCR initialized successfully")
        except ImportError:
            logger.error("PaddleOCR not installed. Install with: pip install paddleocr")
            self.ocr = None
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            self.ocr = None
    
    def extract_text(self, image: np.ndarray) -> Optional['OCRResult']:
        """Extract text from image.
        
        Args:
            image: Input image as numpy array (BGR format)
            
        Returns:
            OCRResult or None if failed
        """
        if self.ocr is None:
            logger.error("PaddleOCR not initialized")
            return None
        
        try:
            start_time = time.time()
            
            # Run OCR
            result = self.ocr.ocr(image, cls=True)
            
            processing_time = time.time() - start_time
            logger.debug(f"PaddleOCR processed in {processing_time:.2f}s")
            
            if not result or not result[0]:
                logger.warning("PaddleOCR returned no results")
                return None
            
            # Convert to OCRResult
            from app.ocr.engine import OCRResult, OCRTextRegion
            
            regions = []
            raw_texts = []
            confidences = []
            
            for line in result[0]:
                if len(line) >= 2:
                    bbox, (text, confidence) = line[0], line[1]
                    
                    regions.append(
                        OCRTextRegion(
                            text=text,
                            confidence=float(confidence),
                            bounding_box=[(float(p[0]), float(p[1])) for p in bbox],
                            engine="paddleocr"
                        )
                    )
                    raw_texts.append(text)
                    confidences.append(float(confidence))
            
            overall_confidence = float(np.mean(confidences)) if confidences else 0.0
            
            ocr_result = OCRResult(
                regions=regions,
                raw_text="\n".join(raw_texts),
                overall_confidence=overall_confidence,
                preprocessing_mode="",
                processing_time_seconds=processing_time
            )
            
            logger.debug(f"Extracted {len(regions)} text regions with avg confidence {overall_confidence:.2f}")
            return ocr_result
            
        except Exception as e:
            logger.error(f"Error extracting text with PaddleOCR: {e}")
            return None
