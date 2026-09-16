"""
Confidence scoring and merging for CauseListOCR
"""

import logging
from typing import List, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class ConfidenceCalculator:
    """Calculate and manage OCR confidence scores."""
    
    @staticmethod
    def field_confidence(
        raw_ocr_confidence: float,
        format_valid: bool = True,
        pattern_match: bool = True,
        consistency_score: float = 1.0
    ) -> float:
        """Calculate confidence for a single field.
        
        Args:
            raw_ocr_confidence: Raw OCR confidence (0.0-1.0)
            format_valid: Is the extracted format valid?
            pattern_match: Does it match expected pattern?
            consistency_score: Consistency with secondary OCR (0.0-1.0)
            
        Returns:
            Weighted confidence score (0.0-1.0)
        """
        confidence = raw_ocr_confidence * 0.5  # 50% from OCR
        
        if format_valid:
            confidence += 0.2  # +20% if format is valid
        
        if pattern_match:
            confidence += 0.15  # +15% if pattern matches
        
        confidence += consistency_score * 0.15  # +15% from consistency
        
        return min(float(confidence), 1.0)
    
    @staticmethod
    def case_number_confidence(
        ocr_confidence: float,
        is_valid_format: bool,
        normalized_successfully: bool,
        secondary_ocr_match: bool = False
    ) -> float:
        """Calculate confidence specifically for case numbers.
        
        Args:
            ocr_confidence: Raw OCR confidence
            is_valid_format: Matches expected case format (e.g., CRLA/72/2024)
            normalized_successfully: Successfully normalized OCR errors
            secondary_ocr_match: Secondary OCR agrees
            
        Returns:
            Confidence score
        """
        score = ocr_confidence * 0.4
        
        if is_valid_format:
            score += 0.35
        
        if normalized_successfully:
            score += 0.15
        
        if secondary_ocr_match:
            score += 0.1
        
        return min(float(score), 1.0)
    
    @staticmethod
    def date_confidence(
        ocr_confidence: float,
        is_valid_date: bool,
        is_logical_date: bool,
        format_match: bool
    ) -> float:
        """Calculate confidence for date fields.
        
        Args:
            ocr_confidence: Raw OCR confidence
            is_valid_date: Is a valid date?
            is_logical_date: Is within reasonable range?
            format_match: Matches expected format (DD-MM-YYYY)
            
        Returns:
            Confidence score
        """
        score = ocr_confidence * 0.4
        
        if format_match:
            score += 0.25
        
        if is_valid_date:
            score += 0.2
        
        if is_logical_date:
            score += 0.15
        
        return min(float(score), 1.0)
    
    @staticmethod
    def text_field_confidence(
        ocr_confidence: float,
        length_reasonable: bool = True,
        contains_special_chars: bool = False
    ) -> float:
        """Calculate confidence for free-text fields.
        
        Args:
            ocr_confidence: Raw OCR confidence
            length_reasonable: Is length within reasonable bounds?
            contains_special_chars: Contains unusual characters?
            
        Returns:
            Confidence score
        """
        score = ocr_confidence * 0.7
        
        if length_reasonable:
            score += 0.2
        
        # Penalize unusual characters
        if contains_special_chars:
            score -= 0.1
        
        return max(min(float(score), 1.0), 0.0)
