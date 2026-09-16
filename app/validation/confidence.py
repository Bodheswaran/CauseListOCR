"""
Confidence assessment for CauseListOCR records
"""

import logging
from typing import Dict, List
from enum import Enum

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Overall record confidence level."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    CRITICAL = "CRITICAL"


class ConfidenceAssessor:
    """Assess overall confidence of extracted records."""
    
    @staticmethod
    def assess_record_confidence(
        case_num_conf: float = 0.9,
        date_conf: float = 0.9,
        party_conf: float = 0.85,
        advocate_conf: float = 0.80,
        validation_issues: List[str] = None
    ) -> Dict[str, any]:
        """Calculate overall confidence for a record.
        
        Args:
            case_num_conf: Case number OCR confidence
            date_conf: Date OCR confidence
            party_conf: Party name OCR confidence
            advocate_conf: Advocate OCR confidence
            validation_issues: List of validation issues found
            
        Returns:
            Dictionary with confidence metrics
        """
        validation_issues = validation_issues or []
        
        # Weighted average
        overall = (
            case_num_conf * 0.40 +  # 40%
            date_conf * 0.30 +      # 30%
            party_conf * 0.20 +     # 20%
            advocate_conf * 0.10    # 10%
        )
        
        # Penalize for validation issues
        for issue in validation_issues:
            if "error" in issue.lower():
                overall *= 0.8  # -20% per error
            elif "warning" in issue.lower():
                overall *= 0.9  # -10% per warning
        
        # Clamp to 0-1
        overall = max(0.0, min(1.0, overall))
        
        # Determine confidence level
        if overall >= 0.85:
            level = ConfidenceLevel.HIGH
        elif overall >= 0.70:
            level = ConfidenceLevel.MEDIUM
        elif overall >= 0.50:
            level = ConfidenceLevel.LOW
        else:
            level = ConfidenceLevel.CRITICAL
        
        requires_review = level in [ConfidenceLevel.LOW, ConfidenceLevel.CRITICAL]
        
        return {
            "overall_confidence": overall,
            "level": level,
            "requires_review": requires_review,
            "reasons": validation_issues,
            "breakdown": {
                "case_number": case_num_conf,
                "date": date_conf,
                "party_name": party_conf,
                "advocate": advocate_conf
            }
        }
    
    @staticmethod
    def batch_assess_records(records: List[Dict]) -> List[Dict]:
        """Assess confidence for multiple records.
        
        Args:
            records: List of extracted records
            
        Returns:
            Records with confidence metrics added
        """
        for rec in records:
            validation_issues = rec.get('validation_issues', [])
            
            confidence_result = ConfidenceAssessor.assess_record_confidence(
                case_num_conf=rec.get('case_number_confidence', 0.7),
                date_conf=rec.get('date_confidence', 0.7),
                party_conf=rec.get('party_name_confidence', 0.7),
                advocate_conf=rec.get('advocate_confidence', 0.6),
                validation_issues=validation_issues
            )
            
            rec['overall_confidence'] = confidence_result['overall_confidence']
            rec['confidence_level'] = confidence_result['level'].value
            rec['needs_review'] = confidence_result['requires_review']
        
        return records
