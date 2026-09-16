"""
Case number extraction and validation for CauseListOCR
Handles multiple case formats with normalization
"""

import re
import logging
from typing import Optional, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ParsedCaseNumber:
    """Parsed case number components."""
    raw_text: str
    prefix: str  # CRLA, SC, CRL, etc.
    number: int  # Case number
    year: int    # Year
    is_valid: bool
    normalized: str  # Normalized format: PREFIX/NUMBER/YEAR
    confidence: float


class CaseNumberParser:
    """Parse and validate case numbers."""
    
    # Supported case prefixes
    CASE_PREFIXES = {
        "CRLA",      # Criminal Appeal
        "CRL",       # Criminal
        "CRLM",      # Criminal Miscellaneous
        "CRL.M.P",   # Criminal Miscellaneous Petition
        "CRL.A",     # Criminal Appeal
        "SC",        # Suomenkielinen Cases (or Supreme Court references)
        "WP",        # Writ Petition
        "WMP",       # Writ Miscellaneous Petition
        "OS",        # Original Suit
        "AS",        # Appeal Suit
        "SA",        # Second Appeal
        "MFA",       # Miscellaneous First Appeal
        "IA",        # Interlocutory Appeal
        "RFA",       # Regular First Appeal
    }
    
    @staticmethod
    def normalize_case_number(raw_text: str) -> Optional[str]:
        """Normalize case number by fixing OCR errors.
        
        Common OCR confusions:
        - O (letter) vs 0 (zero)
        - I (letter) vs 1 (one)  
        - S (letter) vs 5 (five)
        - | (pipe) vs / (slash)
        
        Args:
            raw_text: Raw OCR text
            
        Returns:
            Normalized case number or None if invalid
        """
        text = raw_text.strip().upper()
        
        # Replace common OCR errors
        # Only replace if it makes sense contextually
        replacements = [
            (r'\s+', ''),  # Remove spaces
            (r'[|\\]', '/'),  # Pipe/backslash to slash
        ]
        
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text)
        
        return text
    
    @classmethod
    def parse_case_number(cls, raw_text: str) -> Optional[ParsedCaseNumber]:
        """Parse case number into components.
        
        Expected format: PREFIX/NUMBER/YEAR
        Examples:
        - CRLA/72/2024
        - SC/236/2023
        - WP/123/2025
        
        Args:
            raw_text: Raw OCR text
            
        Returns:
            ParsedCaseNumber or None if invalid
        """
        if not raw_text:
            return None
        
        original = raw_text.strip()
        normalized = cls.normalize_case_number(original)
        
        if not normalized:
            return None
        
        # Pattern to match PREFIX/NUMBER/YEAR
        pattern = r'^([A-Z]+\.?[A-Z]?\.?[A-Z]?)\/([0-9]+)\/([0-9]{4})$'
        match = re.match(pattern, normalized)
        
        if not match:
            logger.debug(f"Case number does not match pattern: {normalized}")
            return None
        
        prefix, number_str, year_str = match.groups()
        
        try:
            number = int(number_str)
            year = int(year_str)
        except ValueError:
            return None
        
        # Validate year (reasonable range: 1950-2100)
        if year < 1950 or year > 2100:
            logger.warning(f"Case number year out of range: {year}")
        
        # Check if prefix is known (warn if unknown)
        prefix_base = prefix.replace('.', '')
        is_valid = prefix_base in cls.CASE_PREFIXES
        
        if not is_valid:
            logger.warning(f"Unknown case prefix: {prefix}")
        
        normalized_case = f"{prefix}/{number}/{year}"
        
        return ParsedCaseNumber(
            raw_text=original,
            prefix=prefix,
            number=number,
            year=year,
            is_valid=is_valid,
            normalized=normalized_case,
            confidence=0.95 if is_valid else 0.70
        )
    
    @classmethod
    def validate_case_number(cls, case_num: ParsedCaseNumber) -> bool:
        """Validate a parsed case number.
        
        Args:
            case_num: Parsed case number
            
        Returns:
            True if valid
        """
        return (
            case_num.is_valid and
            case_num.number > 0 and
            1950 <= case_num.year <= 2100
        )
    
    @classmethod
    def correct_common_ocr_errors(cls, raw_text: str) -> Optional[str]:
        """Attempt to correct common OCR errors in case numbers.
        
        Args:
            raw_text: Raw OCR text
            
        Returns:
            Corrected case number or None
        """
        text = raw_text.strip().upper()
        
        # Try common substitutions
        candidates = [text]
        
        # O/0 confusion
        candidates.append(re.sub(r'O', '0', text))
        candidates.append(re.sub(r'0', 'O', text))
        
        # I/1 confusion
        candidates.append(re.sub(r'I', '1', text))
        candidates.append(re.sub(r'1', 'I', text))
        
        # S/5 confusion
        candidates.append(re.sub(r'S', '5', text))
        candidates.append(re.sub(r'5', 'S', text))
        
        # Try parsing each candidate
        for candidate in candidates:
            parsed = cls.parse_case_number(candidate)
            if parsed and parsed.is_valid:
                logger.info(f"Corrected OCR error: {text} -> {parsed.normalized}")
                return parsed.normalized
        
        return None
