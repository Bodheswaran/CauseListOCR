"""
Field processing and multiline text reconstruction for CauseListOCR
Handles party names, advocate names, and free-text fields
"""

import logging
from typing import List, Optional
import re

logger = logging.getLogger(__name__)


class FieldProcessor:
    """Process and reconstruct multiline text fields."""
    
    @staticmethod
    def join_multiline_text(
        text_lines: List[str],
        preserve_punctuation: bool = True,
        join_char: str = " "
    ) -> str:
        """Join multiple text lines into a single field.
        
        Handles reconstruction of multiline OCR results without losing
        punctuation or structure.
        
        Example:
            Input: ["Dr Rajkumar", "Radhakrishnaan and another Vs Chief", "medical officer"]
            Output: "Dr Rajkumar Radhakrishnaan and another Vs Chief medical officer"
        
        Args:
            text_lines: List of text lines from OCR
            preserve_punctuation: Keep punctuation as-is
            join_char: Character to use for joining (default space)
            
        Returns:
            Joined text
        """
        if not text_lines:
            return ""
        
        # Filter empty lines
        lines = [line.strip() for line in text_lines if line.strip()]
        
        if not lines:
            return ""
        
        if len(lines) == 1:
            return lines[0]
        
        # Join lines
        result = join_char.join(lines)
        
        # Clean up extra spaces
        result = re.sub(r'\s+', ' ', result)
        
        return result.strip()
    
    @staticmethod
    def clean_party_name(text: str) -> str:
        """Clean and normalize party name.
        
        Args:
            text: Raw party name text
            
        Returns:
            Cleaned party name
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize "vs" variations
        text = re.sub(r'\bvs\.?\b', 'Vs', text, flags=re.IGNORECASE)
        
        # Preserve case and punctuation
        return text.strip()
    
    @staticmethod
    def clean_advocate_name(text: str) -> str:
        """Clean and normalize advocate name.
        
        Args:
            text: Raw advocate name text
            
        Returns:
            Cleaned advocate name
        """
        if not text:
            return ""
        
        # Remove excessive whitespace but keep structure
        text = re.sub(r'\s+', ' ', text)
        
        # Handle common abbreviations
        abbreviations = {
            'ADPP': 'ADPP',
            'APP': 'APP',
            'ASP': 'ASP',
            'SP': 'SP',
        }
        
        for abbr, proper in abbreviations.items():
            text = re.sub(rf'\b{abbr}\.?\b', proper, text, flags=re.IGNORECASE)
        
        return text.strip()
    
    @staticmethod
    def validate_text_field(
        text: str,
        min_length: int = 3,
        max_length: int = 500,
        allow_empty: bool = False
    ) -> bool:
        """Validate a text field.
        
        Args:
            text: Text to validate
            min_length: Minimum length
            max_length: Maximum length
            allow_empty: Allow empty/dash fields
            
        Returns:
            True if valid
        """
        if not text or text.strip() in ["-", "--", ""]:
            return allow_empty
        
        length = len(text.strip())
        return min_length <= length <= max_length
    
    @staticmethod
    def normalize_special_characters(text: str) -> str:
        """Normalize special characters while preserving meaning.
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Fix common OCR substitutions
        replacements = [
            ("'", "'"),  # Curly quote to straight
            ("'", "'"),  # Other curly quote
            ('"', '"'),  # Curly double quote
            ('–', '-'),   # En dash to hyphen
            ('—', '-'),   # Em dash to hyphen
        ]
        
        result = text
        for old, new in replacements:
            result = result.replace(old, new)
        
        return result
    
    @staticmethod
    def extract_dash_indicator(text: str) -> bool:
        """Check if field is empty/not available (dash).
        
        Args:
            text: Text to check
            
        Returns:
            True if field is marked as empty (-)
        """
        normalized = text.strip().lower() if text else ""
        return normalized in ["-", "--", "—", "–"]
    
    @classmethod
    def process_multiline_field(
        cls,
        lines: List[str],
        field_type: str = "text"
    ) -> str:
        """Process multiline field based on type.
        
        Args:
            lines: Text lines from OCR
            field_type: Type of field ('party', 'advocate', 'text')
            
        Returns:
            Processed field value
        """
        # Join lines
        joined = cls.join_multiline_text(lines)
        
        if not joined:
            return "-"
        
        # Apply field-specific processing
        if field_type == "party":
            return cls.clean_party_name(joined)
        elif field_type == "advocate":
            return cls.clean_advocate_name(joined)
        else:
            # Generic text processing
            return cls.normalize_special_characters(joined)
