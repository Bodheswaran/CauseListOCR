"""
Field validation for CauseListOCR
Validates extracted fields against business rules
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation result status."""
    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"
    EMPTY = "empty"


@dataclass
class ValidationResult:
    """Result of validating a single field."""
    field_name: str
    value: str
    status: ValidationStatus
    confidence: float
    messages: List[str]
    requires_review: bool


class FieldValidator:
    """Validate extracted record fields."""
    
    @staticmethod
    def validate_case_number(case_number: str, confidence: float) -> ValidationResult:
        """Validate case number field.
        
        Args:
            case_number: Parsed case number (should be PREFIX/NUMBER/YEAR)
            confidence: OCR confidence
            
        Returns:
            ValidationResult
        """
        messages = []
        status = ValidationStatus.VALID
        requires_review = False
        
        if not case_number or case_number.strip() in ["-", ""]:
            return ValidationResult(
                field_name="case_number",
                value=case_number,
                status=ValidationStatus.EMPTY,
                confidence=0.0,
                messages=["Case number is empty"],
                requires_review=True
            )
        
        # Check format PREFIX/NUMBER/YEAR
        import re
        if not re.match(r'^[A-Z]+\.?[A-Z]?\.?[A-Z]?\/\d+\/\d{4}$', case_number):
            messages.append(f"Case number format invalid: {case_number}")
            status = ValidationStatus.ERROR
            requires_review = True
        
        # Check confidence
        if confidence < 0.70:
            messages.append(f"Low OCR confidence: {confidence:.2f}")
            if status == ValidationStatus.VALID:
                status = ValidationStatus.WARNING
            requires_review = True
        
        return ValidationResult(
            field_name="case_number",
            value=case_number,
            status=status,
            confidence=confidence,
            messages=messages,
            requires_review=requires_review
        )
    
    @staticmethod
    def validate_date(date_str: str, confidence: float) -> ValidationResult:
        """Validate date field.
        
        Args:
            date_str: Date in DD-MM-YYYY format
            confidence: OCR confidence
            
        Returns:
            ValidationResult
        """
        messages = []
        status = ValidationStatus.VALID
        requires_review = False
        
        if not date_str or date_str.strip() in ["-", ""]:
            return ValidationResult(
                field_name="hearing_date",
                value=date_str,
                status=ValidationStatus.EMPTY,
                confidence=0.0,
                messages=["Date is empty"],
                requires_review=True
            )
        
        # Check format DD-MM-YYYY
        import re
        if not re.match(r'^\d{2}-\d{2}-\d{4}$', date_str):
            messages.append(f"Date format invalid: {date_str} (expected DD-MM-YYYY)")
            status = ValidationStatus.ERROR
            requires_review = True
        
        # Validate date is logical
        from app.parsing.dates import DateParser
        parsed = DateParser.parse_date(date_str)
        if parsed and not parsed.is_valid:
            messages.append(f"Date is invalid: {date_str}")
            status = ValidationStatus.ERROR
            requires_review = True
        elif parsed and not DateParser.is_logical_date(parsed.date_obj):
            messages.append(f"Date is not logical: {date_str}")
            status = ValidationStatus.WARNING
            requires_review = True
        
        if confidence < 0.70:
            messages.append(f"Low OCR confidence: {confidence:.2f}")
            if status == ValidationStatus.VALID:
                status = ValidationStatus.WARNING
            requires_review = True
        
        return ValidationResult(
            field_name="hearing_date",
            value=date_str,
            status=status,
            confidence=confidence,
            messages=messages,
            requires_review=requires_review
        )
    
    @staticmethod
    def validate_party_name(party_name: str, confidence: float, allow_empty: bool = False) -> ValidationResult:
        """Validate party name field.
        
        Args:
            party_name: Party name text
            confidence: OCR confidence
            allow_empty: Allow empty field
            
        Returns:
            ValidationResult
        """
        messages = []
        status = ValidationStatus.VALID
        requires_review = False
        
        if not party_name or party_name.strip() in ["-", ""]:
            if allow_empty:
                return ValidationResult(
                    field_name="party_name",
                    value="-",
                    status=ValidationStatus.EMPTY,
                    confidence=1.0,
                    messages=["Party name is empty"],
                    requires_review=False
                )
            else:
                return ValidationResult(
                    field_name="party_name",
                    value=party_name,
                    status=ValidationStatus.ERROR,
                    confidence=0.0,
                    messages=["Party name is required but empty"],
                    requires_review=True
                )
        
        # Check length
        length = len(party_name.strip())
        if length < 3:
            messages.append(f"Party name too short: {length} chars")
            status = ValidationStatus.ERROR
            requires_review = True
        elif length > 500:
            messages.append(f"Party name too long: {length} chars")
            status = ValidationStatus.WARNING
            requires_review = True
        
        # Check for unusual characters
        import re
        if re.search(r'[^a-zA-Z0-9\s.,()\'\-&]', party_name):
            messages.append(f"Party name contains unusual characters")
            if status == ValidationStatus.VALID:
                status = ValidationStatus.WARNING
            requires_review = True
        
        if confidence < 0.70:
            messages.append(f"Low OCR confidence: {confidence:.2f}")
            requires_review = True
        
        return ValidationResult(
            field_name="party_name",
            value=party_name,
            status=status,
            confidence=confidence,
            messages=messages,
            requires_review=requires_review
        )
    
    @staticmethod
    def validate_advocate(advocate: str, confidence: float, allow_empty: bool = True) -> ValidationResult:
        """Validate advocate field.
        
        Args:
            advocate: Advocate name or "-"
            confidence: OCR confidence
            allow_empty: Allow empty field
            
        Returns:
            ValidationResult
        """
        messages = []
        status = ValidationStatus.VALID
        requires_review = False
        
        if not advocate or advocate.strip() in ["-", ""]:
            if allow_empty:
                return ValidationResult(
                    field_name="advocate",
                    value="-",
                    status=ValidationStatus.EMPTY,
                    confidence=1.0,
                    messages=["Advocate not specified"],
                    requires_review=False
                )
            else:
                return ValidationResult(
                    field_name="advocate",
                    value=advocate,
                    status=ValidationStatus.ERROR,
                    confidence=0.0,
                    messages=["Advocate is required but empty"],
                    requires_review=True
                )
        
        # Similar checks as party name
        length = len(advocate.strip())
        if length < 2:
            messages.append(f"Advocate name too short: {length} chars")
            status = ValidationStatus.WARNING
            requires_review = True
        elif length > 300:
            messages.append(f"Advocate name too long: {length} chars")
            status = ValidationStatus.WARNING
            requires_review = True
        
        if confidence < 0.70:
            messages.append(f"Low OCR confidence: {confidence:.2f}")
            requires_review = True
        
        return ValidationResult(
            field_name="advocate",
            value=advocate,
            status=status,
            confidence=confidence,
            messages=messages,
            requires_review=requires_review
        )
