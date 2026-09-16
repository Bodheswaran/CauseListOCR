"""
Data models and classes for CauseListOCR
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ConfidenceLevel(Enum):
    """OCR confidence classification."""
    HIGH = "HIGH"      # >= 0.85
    MEDIUM = "MEDIUM"  # 0.70-0.84
    LOW = "LOW"        # < 0.70


@dataclass
class ExtractedField:
    """Single extracted field with confidence and audit trail."""
    raw_text: str  # Original OCR output
    final_text: str  # Normalized/corrected value
    confidence: float  # 0.0-1.0
    ocr_engine: str  # "paddleocr", "tesseract", etc.
    review_required: bool = False
    bounding_box: Optional[List[float]] = None  # [x, y, w, h]
    source_image_path: Optional[str] = None
    notes: str = ""
    
    def confidence_level(self) -> ConfidenceLevel:
        """Determine confidence classification."""
        if self.confidence >= 0.85:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.70:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW


@dataclass
class CaseRecord:
    """Complete case record extracted from Cause List."""
    case_number: ExtractedField
    hearing_date: ExtractedField
    party_name: ExtractedField
    advocate: ExtractedField
    
    # Metadata
    source_image_path: str
    source_region: Optional[Dict[str, Any]] = None  # Bounding box in original image
    extracted_at: datetime = field(default_factory=datetime.now)
    
    # Review
    overall_confidence: float = 0.0
    needs_human_review: bool = False
    user_review_status: Optional[str] = None  # "approved", "rejected", "edited"
    user_edits: Dict[str, str] = field(default_factory=dict)
    
    # Duplicate detection
    is_duplicate: bool = False
    duplicate_of_case_number: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Check if record meets minimum validation."""
        # Case number and date are mandatory
        return bool(self.case_number.final_text) and bool(self.hearing_date.final_text)
    
    def calculate_overall_confidence(self) -> float:
        """Calculate weighted average confidence."""
        fields = [
            (self.case_number.confidence, 0.4),      # 40%
            (self.hearing_date.confidence, 0.3),     # 30%
            (self.party_name.confidence, 0.2),       # 20%
            (self.advocate.confidence, 0.1),         # 10%
        ]
        weighted_sum = sum(conf * weight for conf, weight in fields)
        self.overall_confidence = weighted_sum
        return weighted_sum


@dataclass
class ProcessingResult:
    """Result of processing a single image."""
    image_path: str
    success: bool
    records: List[CaseRecord] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time_seconds: float = 0.0
    
    def record_count(self) -> int:
        """Total records extracted."""
        return len(self.records)
    
    def high_confidence_count(self) -> int:
        """Records with high confidence."""
        return sum(1 for r in self.records if r.overall_confidence >= 0.85)
    
    def needs_review_count(self) -> int:
        """Records flagged for review."""
        return sum(1 for r in self.records if r.needs_human_review or r.user_review_status == "edited")


@dataclass
class BatchProcessingResult:
    """Result of processing multiple images."""
    image_results: List[ProcessingResult] = field(default_factory=list)
    total_time_seconds: float = 0.0
    duplicates_found: List[tuple] = field(default_factory=list)  # List of (case_num, sources)
    
    def all_records(self) -> List[CaseRecord]:
        """Get all records from all images."""
        all_recs: List[CaseRecord] = []
        for result in self.image_results:
            all_recs.extend(result.records)
        return all_recs
    
    def total_records(self) -> int:
        """Total records across all images."""
        return sum(r.record_count() for r in self.image_results)
    
    def total_high_confidence(self) -> int:
        """Total high-confidence records."""
        return sum(r.high_confidence_count() for r in self.image_results)
    
    def total_needs_review(self) -> int:
        """Total records needing review."""
        return sum(r.needs_review_count() for r in self.image_results)
