"""
Duplicate detection for CauseListOCR
Identifies duplicate case numbers and similar records
"""

import logging
from typing import List, Tuple, Dict, Set
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """Detect duplicate case records."""
    
    @staticmethod
    def find_duplicate_case_numbers(case_numbers: List[str]) -> List[Tuple[str, str, int]]:
        """Find exact duplicate case numbers.
        
        Args:
            case_numbers: List of case numbers
            
        Returns:
            List of (case1, case2, occurrence_count) tuples
        """
        from collections import Counter
        
        counts = Counter(case_numbers)
        duplicates = []
        
        for case_num, count in counts.items():
            if count > 1:
                duplicates.append((case_num, case_num, count))
                logger.warning(f"Duplicate case number found: {case_num} ({count} occurrences)")
        
        return duplicates
    
    @staticmethod
    def find_similar_case_numbers(
        case_numbers: List[str],
        threshold: float = 0.85
    ) -> List[Tuple[str, str, float]]:
        """Find similar case numbers (possible OCR errors).
        
        Example: CRLA/72/2024 vs CRLA/73/2024 (typo in case number)
        
        Args:
            case_numbers: List of case numbers
            threshold: Similarity threshold (0.0-1.0)
            
        Returns:
            List of (case1, case2, similarity) tuples
        """
        similar_pairs = []
        
        for i, case1 in enumerate(case_numbers):
            for case2 in case_numbers[i + 1:]:
                if case1 != case2:
                    # Use token_set_ratio for better matching
                    similarity = fuzz.token_set_ratio(case1, case2) / 100.0
                    
                    if similarity >= threshold:
                        similar_pairs.append((case1, case2, similarity))
                        logger.info(f"Similar case numbers: {case1} ~ {case2} ({similarity:.2f})")
        
        return similar_pairs
    
    @staticmethod
    def find_similar_records(
        records: List[Dict],
        threshold: float = 0.9
    ) -> List[Tuple[int, int, float]]:
        """Find similar records (possible exact duplicates).
        
        Compares party names and case numbers.
        
        Args:
            records: List of extracted records
            threshold: Similarity threshold
            
        Returns:
            List of (record_idx1, record_idx2, similarity) tuples
        """
        similar_pairs = []
        
        for i, rec1 in enumerate(records):
            for j, rec2 in enumerate(records[i + 1:], i + 1):
                # Compare case numbers (exact)
                case_match = rec1.get('case_number', '') == rec2.get('case_number', '')
                
                if case_match:
                    # Case numbers match - high likelihood of duplicate
                    party1 = rec1.get('party_name', '')
                    party2 = rec2.get('party_name', '')
                    
                    # Compare party names
                    party_sim = fuzz.token_set_ratio(party1, party2) / 100.0
                    
                    overall_sim = 0.7 * (1.0 if case_match else 0.0) + 0.3 * party_sim
                    
                    if overall_sim >= threshold:
                        similar_pairs.append((i, j, overall_sim))
                        logger.warning(
                            f"Potential duplicate records: "
                            f"#{i} ({rec1.get('case_number', 'unknown')}) ~ "
                            f"#{j} ({rec2.get('case_number', 'unknown')}) "
                            f"({overall_sim:.2f})"
                        )
        
        return similar_pairs
    
    @staticmethod
    def get_unique_case_numbers(case_numbers: List[str]) -> Set[str]:
        """Get set of unique case numbers.
        
        Args:
            case_numbers: List of case numbers
            
        Returns:
            Set of unique case numbers
        """
        return set(case_numbers)
    
    @staticmethod
    def mark_duplicates(records: List[Dict]) -> List[Dict]:
        """Mark duplicate records in place.
        
        Args:
            records: List of records to mark
            
        Returns:
            Records with 'is_duplicate' and 'duplicate_of' fields set
        """
        # Find exact duplicates by case number
        case_num_to_indices: Dict[str, List[int]] = {}
        
        for idx, rec in enumerate(records):
            case_num = rec.get('case_number', '')
            if case_num:
                if case_num not in case_num_to_indices:
                    case_num_to_indices[case_num] = []
                case_num_to_indices[case_num].append(idx)
        
        # Mark duplicates (keep first occurrence)
        for case_num, indices in case_num_to_indices.items():
            if len(indices) > 1:
                for idx in indices[1:]:
                    records[idx]['is_duplicate'] = True
                    records[idx]['duplicate_of'] = indices[0]  # First occurrence
                    logger.info(f"Marked record #{idx} as duplicate of #{indices[0]}")
        
        return records
