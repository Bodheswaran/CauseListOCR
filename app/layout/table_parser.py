"""
Table parser for cause list extraction
Combines row and column detection to parse table structure
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TableCell:
    """Single cell in a table."""
    content: str
    row_idx: int
    col_idx: int
    confidence: float
    raw_ocr: str


@dataclass
class TableStructure:
    """Parsed table structure."""
    rows: int
    cols: int
    cells: List[TableCell]
    column_headers: Optional[List[str]] = None
    header_row_idx: Optional[int] = None
    
    def get_cell(self, row: int, col: int) -> Optional[TableCell]:
        """Get cell at specific position.
        
        Args:
            row: Row index
            col: Column index
            
        Returns:
            TableCell or None
        """
        for cell in self.cells:
            if cell.row_idx == row and cell.col_idx == col:
                return cell
        return None
    
    def get_row(self, row: int) -> List[TableCell]:
        """Get all cells in a row.
        
        Args:
            row: Row index
            
        Returns:
            List of cells in that row
        """
        return [cell for cell in self.cells if cell.row_idx == row]


class TableParser:
    """Parse table structure from OCR results."""
    
    @staticmethod
    def detect_header_row(rows: List[List[Dict]]) -> Optional[int]:
        """Detect which row is the header.
        
        Args:
            rows: List of rows with OCR regions
            
        Returns:
            Index of header row or None
        """
        if not rows:
            return None
        
        # Common header keywords for cause lists
        header_keywords = ["Case", "Number", "Party", "Advocate", "Sr", "No", "Date", "Hearing"]
        
        for idx, row in enumerate(rows):
            row_text = " ".join([region.get('text', '') for region in row]).lower()
            
            keyword_matches = sum(1 for keyword in header_keywords if keyword.lower() in row_text)
            
            # If row contains multiple header keywords, likely a header
            if keyword_matches >= 2:
                logger.info(f"Detected header row at index {idx}")
                return idx
        
        # Default to first row
        return 0
    
    @staticmethod
    def extract_column_headers(header_row: List[Dict]) -> List[str]:
        """Extract column headers from header row.
        
        Args:
            header_row: List of regions in header row
            
        Returns:
            List of column header names
        """
        headers = []
        for region in header_row:
            text = region.get('text', '').strip()
            if text:
                headers.append(text)
        
        logger.debug(f"Extracted headers: {headers}")
        return headers
    
    @staticmethod
    def parse_table(
        rows: List[List[Dict]],
        expected_columns: int = 4
    ) -> TableStructure:
        """Parse complete table structure.
        
        Args:
            rows: Rows of OCR regions
            expected_columns: Expected number of columns
            
        Returns:
            Parsed table structure
        """
        if not rows:
            return TableStructure(rows=0, cols=0, cells=[])
        
        # Detect header
        header_idx = TableParser.detect_header_row(rows)
        headers = None
        if header_idx is not None and header_idx < len(rows):
            headers = TableParser.extract_column_headers(rows[header_idx])
        
        # Parse cells
        cells = []
        for row_idx, row in enumerate(rows):
            # Skip header row
            if row_idx == header_idx:
                continue
            
            for col_idx, region in enumerate(row):
                if col_idx >= expected_columns:
                    break
                
                cell = TableCell(
                    content=region.get('text', '').strip(),
                    row_idx=row_idx,
                    col_idx=col_idx,
                    confidence=region.get('confidence', 0.0),
                    raw_ocr=region.get('raw_text', '')
                )
                cells.append(cell)
        
        table = TableStructure(
            rows=len(rows),
            cols=expected_columns,
            cells=cells,
            column_headers=headers,
            header_row_idx=header_idx
        )
        
        logger.info(f"Parsed table: {table.rows} rows × {table.cols} columns")
        return table
    
    @staticmethod
    def identify_section_headings(rows: List[List[Dict]]) -> List[int]:
        """Identify rows that are section headings (not data).
        
        Example headings:
        - Arguments
        - Judgement
        - For Orders
        - Await Records
        
        Args:
            rows: List of rows with OCR regions
            
        Returns:
            List of row indices that are headings
        """
        section_keywords = [
            "Arguments", "Judgement", "For Orders", "Await Records",
            "For Further Proceedings", "Admission", "CMP Pending",
            "Service Pending", "Steps", "For Hearing", "Disposal"
        ]
        
        heading_rows = []
        for idx, row in enumerate(rows):
            if not row:
                heading_rows.append(idx)
                continue
            
            # If row has only one cell and it matches a section keyword
            if len(row) == 1:
                text = row[0].get('text', '').strip()
                if any(keyword in text for keyword in section_keywords):
                    heading_rows.append(idx)
            elif len(row) <= 2:
                # Check if combined text matches
                combined = " ".join([r.get('text', '') for r in row]).strip()
                if any(keyword in combined for keyword in section_keywords):
                    heading_rows.append(idx)
        
        logger.info(f"Identified {len(heading_rows)} section heading rows")
        return heading_rows
