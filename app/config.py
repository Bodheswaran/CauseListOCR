"""
Application configuration
"""

import os


class Config:
    """Base configuration."""
    DEBUG = False
    TESTING = False
    JSON_SORT_KEYS = False
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///causelist_ocr.db')
    OCR_ENGINE = os.environ.get('OCR_ENGINE', 'tesseract')


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'
    OCR_ENGINE = 'tesseract'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    DATABASE_URL = os.environ.get('DATABASE_URL')
    OCR_ENGINE = os.environ.get('OCR_ENGINE', 'textract')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
