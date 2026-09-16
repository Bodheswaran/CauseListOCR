"""
Date parsing and validation for CauseListOCR
Handles DD-MM-YYYY format with validation
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParsedDate:
    """Parsed and validated date."""
    raw_text: str
    day: int
    month: int
    year: int
    is_valid: bool
    formatted: str  # DD-MM-YYYY
    date_obj: Optional[datetime] = None
    confidence: float = 0.0


class DateParser:
    """Parse and validate hearing dates."""
    
    @staticmethod
    def parse_date(raw_text: str, expected_format: str = "DD-MM-YYYY") -> Optional[ParsedDate]:
        """Parse date from OCR text.
        
        Expected format: DD-MM-YYYY
        Examples: 16-09-2026, 01-01-2024
        
        Args:
            raw_text: Raw OCR text
            expected_format: Expected date format
            
        Returns:
            ParsedDate or None if invalid
        """
        if not raw_text:
            return None
        
        text = raw_text.strip()
        
        # Pattern for DD-MM-YYYY
        pattern = r'^(\d{1,2})[-/\.]?(\d{1,2})[-/\.]?(\d{4})$'
        match = re.match(pattern, text)
        
        if not match:
            logger.debug(f"Date does not match pattern: {text}")
            return None
        
        day_str, month_str, year_str = match.groups()
        
        try:
            day = int(day_str)
            month = int(month_str)
            year = int(year_str)
        except ValueError:
            return None
        
        # Validate date components
        is_valid = DateParser._validate_date_components(day, month, year)
        
        if not is_valid:
            logger.warning(f"Invalid date components: {day}-{month}-{year}")
        
        # Try to create date object
        date_obj = None
        if is_valid:
            try:
                date_obj = datetime(year, month, day)
            except ValueError:
                is_valid = False
                logger.warning(f"Invalid date: {day}-{month}-{year}")
        
        formatted = f"{day:02d}-{month:02d}-{year}"
        
        return ParsedDate(
            raw_text=text,
            day=day,
            month=month,
            year=year,
            is_valid=is_valid,
            formatted=formatted,
            date_obj=date_obj,
            confidence=0.95 if is_valid else 0.50
        )
    
    @staticmethod
    def _validate_date_components(day: int, month: int, year: int) -> bool:
        """Validate date components.
        
        Args:
            day: Day (1-31)
            month: Month (1-12)
            year: Year (1950-2100)
            
        Returns:
            True if valid
        """
        # Check ranges
        if not (1 <= day <= 31):
            return False
        if not (1 <= month <= 12):
            return False
        if not (1950 <= year <= 2100):
            return False
        
        # Days per month
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        
        # Check for leap year
        is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        if is_leap:
            days_in_month[1] = 29
        
        # Validate day for month
        if day > days_in_month[month - 1]:
            return False
        
        return True
    
    @staticmethod
    def is_logical_date(date_obj: datetime) -> bool:
        """Check if date is logically reasonable.
        
        For court cases, dates should be:
        - Not in the future (or very close)
        - Not too far in the past
        
        Args:
            date_obj: Date object
            
        Returns:
            True if logical
        """
        now = datetime.now()
        
        # Allow dates up to 1 year in future (for scheduled hearings)
        future_threshold = now + timedelta(days=365)
        if date_obj > future_threshold:
            return False
        
        # Reject dates before 1950
        if date_obj.year < 1950:
            return False
        
        return True
    
    @staticmethod
    def correct_ocr_errors(raw_text: str) -> Optional[str]:
        """Attempt to correct common OCR errors in dates.
        
        Common errors:
        - O/0 confusion in year
        - 1/l/I confusion in day/month
        - Space/dash confusion
        
        Args:
            raw_text: Raw OCR text
            
        Returns:
            Corrected date string or None
        """
        text = raw_text.strip()
        
        # Normalize separators
        text = re.sub(r'[/-]', '-', text)
        
        # Try parsing directly
        parsed = DateParser.parse_date(text)
        if parsed and parsed.is_valid:
            return parsed.formatted
        
        # Try common substitutions
        candidates = [text]
        
        # O/0 confusion
        candidates.append(re.sub(r'O', '0', text))
        candidates.append(re.sub(r'0', 'O', text))
        
        # 1/I confusion
        candidates.append(re.sub(r'I', '1', text))
        candidates.append(re.sub(r'1', 'I', text))
        
        for candidate in candidates:
            parsed = DateParser.parse_date(candidate)
            if parsed and parsed.is_valid:
                logger.info(f"Corrected date OCR error: {text} -> {parsed.formatted}")
                return parsed.formatted
        
        return None
