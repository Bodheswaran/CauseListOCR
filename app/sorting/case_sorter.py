"""
Natural sorting for case numbers and cause lists
Handles proper sorting of alphanumeric case identifiers
"""

import re
import logging
from typing import List, Dict, Tuple, Any
from functools import cmp_to_key

logger = logging.getLogger(__name__)


class CaseSorter:
    """Sort case records by various criteria."""
    
    @staticmethod
    def natural_sort_key(text: str) -> Tuple[Any, ...]:
        """Generate natural sort key for alphanumeric text.
        
        Converts text into a tuple of mixed int/str for proper sorting.
        Example: "Case 123" sorts before "Case 45"
        
        Args:
            text: Text to convert
            
        Returns:
            Tuple for sorting
        """
        def convert(part):
            return int(part) if part.isdigit() else part.lower()
        
        return tuple(convert(part) for part in re.split(r'(\d+)', text))
    
    @staticmethod
    def parse_case_number_for_sorting(case_number: str) -> Tuple[str, int, int]:
        """Parse case number into sortable components.
        
        Expected format: PREFIX/NUMBER/YEAR
        Returns: (prefix, number_as_int, year_as_int)
        
        Args:
            case_number: Case number string
            
        Returns:
            Tuple of (prefix, number, year) for sorting
        """
        if not case_number or case_number.strip() in ["-", ""]:
            return ("", 0, 0)
        
        # Pattern: PREFIX/NUMBER/YEAR
        match = re.match(r'^([A-Z]+\.?[A-Z]?\.?[A-Z]?)\/([0-9]+)\/([0-9]{4})$', case_number.strip())
        
        if match:
            prefix, number_str, year_str = match.groups()
            try:
                return (prefix, int(number_str), int(year_str))
            except ValueError:
                return (case_number, 0, 0)
        
        # Fallback for unparseable numbers
        return (case_number, 0, 0)
    
    @classmethod
    def sort_by_case_number(
        cls,
        records: List[Dict],
        reverse: bool = False
    ) -> List[Dict]:
        """Sort records by case number.
        
        Sorts by: Prefix (alphabetical) -> Number (numeric) -> Year (numeric)
        
        Args:
            records: List of records with 'case_number' field
            reverse: Reverse sort order
            
        Returns:
            Sorted records
        """
        def sort_key(record):
            case_num = record.get('case_number', '')
            return cls.parse_case_number_for_sorting(case_num)
        
        sorted_records = sorted(records, key=sort_key, reverse=reverse)
        logger.info(f"Sorted {len(sorted_records)} records by case number")
        return sorted_records
    
    @classmethod
    def sort_by_date(
        cls,
        records: List[Dict],
        reverse: bool = False
    ) -> List[Dict]:
        """Sort records by hearing date.
        
        Args:
            records: List of records with 'hearing_date' field (DD-MM-YYYY)
            reverse: Reverse sort order
            
        Returns:
            Sorted records
        """
        def date_sort_key(record):
            date_str = record.get('hearing_date', '')
            if not date_str or date_str.strip() in ["-", ""]:
                return (9999, 99, 99)  # Sort empty dates to end
            
            try:
                parts = date_str.split('-')
                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                return (year, month, day)  # Sort by YYYY-MM-DD
            except (ValueError, IndexError):
                return (9999, 99, 99)
        
        sorted_records = sorted(records, key=date_sort_key, reverse=reverse)
        logger.info(f"Sorted {len(sorted_records)} records by date")
        return sorted_records
    
    @classmethod
    def sort_by_party_name(
        cls,
        records: List[Dict],
        reverse: bool = False
    ) -> List[Dict]:
        """Sort records by party name alphabetically.
        
        Args:
            records: List of records with 'party_name' field
            reverse: Reverse sort order
            
        Returns:
            Sorted records
        """
        def party_sort_key(record):
            party = record.get('party_name', '')
            return cls.natural_sort_key(party)
        
        sorted_records = sorted(records, key=party_sort_key, reverse=reverse)
        logger.info(f"Sorted {len(sorted_records)} records by party name")
        return sorted_records
    
    @classmethod
    def sort_by_multiple_fields(
        cls,
        records: List[Dict],
        sort_order: List[Tuple[str, bool]] = None
    ) -> List[Dict]:
        """Sort records by multiple fields in order.
        
        Args:
            records: List of records
            sort_order: List of (field_name, reverse) tuples
                       Example: [("case_number", False), ("hearing_date", False)]
            
        Returns:
            Sorted records
        """
        sort_order = sort_order or [("case_number", False)]
        
        # Build composite sort key
        def multi_sort_key(record):
            keys = []
            for field, _ in sort_order:
                if field == "case_number":
                    keys.append(cls.parse_case_number_for_sorting(
                        record.get('case_number', '')
                    ))
                elif field == "hearing_date":
                    date_str = record.get('hearing_date', '')
                    if not date_str or date_str.strip() in ["-", ""]:
                        keys.append((9999, 99, 99))
                    else:
                        try:
                            parts = date_str.split('-')
                            keys.append((int(parts[2]), int(parts[1]), int(parts[0])))
                        except (ValueError, IndexError):
                            keys.append((9999, 99, 99))
                elif field == "party_name":
                    keys.append(cls.natural_sort_key(record.get(field, '')))
                else:
                    keys.append(cls.natural_sort_key(record.get(field, '')))
            return tuple(keys)
        
        sorted_records = sorted(records, key=multi_sort_key)
        
        # Apply reverse for each field
        for field, reverse in reversed(sort_order):
            if reverse:
                sorted_records.reverse()
        
        logger.info(f"Sorted {len(sorted_records)} records by multiple fields: {sort_order}")
        return sorted_records
    
    @staticmethod
    def group_by_field(records: List[Dict], field: str) -> Dict[str, List[Dict]]:
        """Group records by a specific field value.
        
        Args:
            records: List of records
            field: Field name to group by
            
        Returns:
            Dictionary mapping field values to record lists
        """
        groups: Dict[str, List[Dict]] = {}
        
        for record in records:
            value = record.get(field, 'unknown')
            if value not in groups:
                groups[value] = []
            groups[value].append(record)
        
        logger.info(f"Grouped {len(records)} records by '{field}' into {len(groups)} groups")
        return groups
    
    @classmethod
    def group_and_sort(
        cls,
        records: List[Dict],
        group_field: str,
        sort_field: str = "case_number"
    ) -> Dict[str, List[Dict]]:
        """Group records and sort each group.
        
        Example: Group by case prefix, sort each group by case number
        
        Args:
            records: List of records
            group_field: Field to group by
            sort_field: Field to sort within each group
            
        Returns:
            Dictionary of sorted groups
        """
        groups = cls.group_by_field(records, group_field)
        
        # Sort each group
        sorted_groups = {}
        for key in sorted(groups.keys()):
            if sort_field == "case_number":
                sorted_groups[key] = cls.sort_by_case_number(groups[key])
            elif sort_field == "hearing_date":
                sorted_groups[key] = cls.sort_by_date(groups[key])
            elif sort_field == "party_name":
                sorted_groups[key] = cls.sort_by_party_name(groups[key])
            else:
                sorted_groups[key] = sorted(
                    groups[key],
                    key=lambda r: cls.natural_sort_key(r.get(sort_field, ''))
                )
        
        logger.info(f"Grouped and sorted {len(records)} records")
        return sorted_groups
