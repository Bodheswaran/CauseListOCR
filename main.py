#!/usr/bin/env python3
"""
CauseListOCR - Main Application Entry Point
Production-grade offline District Court Cause List OCR to Excel converter
Python 3.14 compatible
"""

import sys
import logging
from pathlib import Path

# Ensure Python 3.14+
if sys.version_info < (3, 14):
    print(f"ERROR: Python 3.14+ required. You have {sys.version_info.major}.{sys.version_info.minor}")
    sys.exit(1)

from app.gui.main_window import MainWindow
from app.utils.logger import setup_logger
from PySide6.QtWidgets import QApplication


def main() -> int:
    """Application entry point."""
    # Setup logging
    logger = setup_logger()
    logger.info(f"CauseListOCR v1.0.0 starting on Python {sys.version_info.major}.{sys.version_info.minor}")
    
    try:
        # Create Qt Application
        app = QApplication(sys.argv)
        
        # Set application metadata
        app.setApplicationName("CauseListOCR")
        app.setApplicationVersion("1.0.0")
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        logger.info("Main window displayed")
        
        # Run event loop
        return app.exec()
        
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        print(f"\nFATAL ERROR: {e}")
        print("See logs/app.log for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
