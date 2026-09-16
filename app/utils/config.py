"""
Configuration management for CauseListOCR
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List
from enum import Enum


class OCRMode(Enum):
    """OCR preprocessing mode selection."""
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
    AUTO = "auto"  # Automatically select best mode


class SortMode(Enum):
    """Case number sorting mode."""
    PREFIX_NUMBER_YEAR = "prefix_number_year"  # Default
    NUMBER_ONLY = "number_only"
    ORIGINAL_ORDER = "original_order"


class DuplicateHandling(Enum):
    """Duplicate case handling strategy."""
    KEEP_ALL = "keep_all"
    REMOVE_EXACT = "remove_exact"
    REVIEW = "review"  # Default


@dataclass
class OCRConfig:
    """OCR engine configuration."""
    use_paddle: bool = True
    use_secondary: bool = False  # Future: Tesseract, EasyOCR, etc.
    confidence_threshold_high: float = 0.85
    confidence_threshold_medium: float = 0.70
    preprocess_mode: OCRMode = OCRMode.AUTO
    use_angle_correction: bool = True
    languages: List[str] = field(default_factory=lambda: ["en"])
    use_gpu: bool = False  # Disable GPU to ensure CPU compatibility


@dataclass
class ValidationConfig:
    """Field validation configuration."""
    require_case_number: bool = True
    require_hearing_date: bool = True
    require_party_name: bool = True
    allow_empty_advocate: bool = True
    validate_case_format: bool = True
    validate_date_format: bool = True


@dataclass
class ExportConfig:
    """Excel export configuration."""
    include_audit_sheet: bool = True
    freeze_header_row: bool = True
    enable_autofilter: bool = True
    header_bg_color: str = "0070C0"  # Blue
    header_text_color: str = "FFFFFF"  # White
    wrap_text: bool = True
    auto_column_width: bool = True


@dataclass
class AppConfig:
    """Application-wide configuration."""
    app_name: str = "CauseListOCR"
    version: str = "1.0.0"
    
    # Processing
    ocr: OCRConfig = field(default_factory=OCRConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    
    # Behavior
    sort_mode: SortMode = SortMode.PREFIX_NUMBER_YEAR
    duplicate_handling: DuplicateHandling = DuplicateHandling.REVIEW
    
    # UI
    window_width: int = 1200
    window_height: int = 800
    theme: str = "light"  # or "dark"
    
    # Logging
    log_level: str = "INFO"
    log_file_retention_days: int = 30
    
    # File handling
    temp_dir: Path = field(default_factory=lambda: Path("./temp"))
    supported_formats: List[str] = field(default_factory=lambda: [".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff", ".tif"])
    max_image_size_mb: int = 20
    
    # Performance
    batch_size: int = 5
    num_threads: int = 4


# Global config instance
default_config = AppConfig()
