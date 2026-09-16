"""
Windows-safe path utilities for CauseListOCR
"""

from pathlib import Path
from typing import Optional


class AppPaths:
    """Centralized path management (Windows-safe)."""
    
    # Base directories
    APP_DIR = Path(__file__).parent.parent.parent  # Project root
    MODELS_DIR = APP_DIR / "models"
    LOGS_DIR = APP_DIR / "logs"
    OUTPUT_DIR = APP_DIR / "output"
    SAMPLES_DIR = APP_DIR / "samples"
    TESTS_DIR = APP_DIR / "tests"
    
    @classmethod
    def ensure_dirs(cls) -> None:
        """Create all required directories."""
        for directory in [cls.MODELS_DIR, cls.LOGS_DIR, cls.OUTPUT_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_models_dir(cls) -> Path:
        """Get OCR models directory."""
        return cls.MODELS_DIR
    
    @classmethod
    def get_logs_dir(cls) -> Path:
        """Get logs directory."""
        return cls.LOGS_DIR
    
    @classmethod
    def get_output_dir(cls) -> Path:
        """Get output Excel directory."""
        return cls.OUTPUT_DIR
    
    @classmethod
    def get_latest_excel(cls) -> Optional[Path]:
        """Get the most recent Excel output file."""
        xlsx_files = list(cls.OUTPUT_DIR.glob("Cause_List_*.xlsx"))
        if not xlsx_files:
            return None
        return sorted(xlsx_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
