"""
Column detection for cause list tables
Identifies vertical alignment and groups columns
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class ColumnDetector:
    """Detect and identify table columns."""
    
    @staticmethod
    def detect_vertical_lines(image: np.ndarray, threshold: int = 100) -> List[Tuple[int, int, int, int]]:
        """Detect vertical lines in image.
        
        Args:
            image: Input image (BGR or grayscale)
            threshold: Threshold for line detection
            
        Returns:
            List of lines as (x1, y1, x2, y2)
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply binary threshold
        _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)
        
        # Detect vertical lines
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(vertical_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        lines = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if h > 50:  # Minimum line height
                lines.append((x, y, x + w, y + h))
        
        return sorted(lines, key=lambda l: l[0])  # Sort by x coordinate
    
    @staticmethod
    def extract_column_boundaries(bboxes: List[Tuple[int, int, int, int]]) -> List[float]:
        """Extract column boundaries from bounding boxes.
        
        Args:
            bboxes: List of bounding boxes (x_min, y_min, x_max, y_max)
            
        Returns:
            List of x-coordinates representing column boundaries
        """
        if not bboxes:
            return []
        
        # Get all x coordinates
        x_coords = []
        for bbox in bboxes:
            x_coords.append(bbox[0])  # x_min
            x_coords.append(bbox[2])  # x_max
        
        # Cluster similar x coordinates
        x_coords.sort()
        boundaries = [x_coords[0]]
        
        for x in x_coords[1:]:
            # If x is far from last boundary, add new boundary
            if x - boundaries[-1] > 30:  # Threshold for new column
                boundaries.append(x)
        
        return boundaries
    
    @staticmethod
    def assign_to_columns(
        bboxes: List[Tuple[int, int, int, int]],
        column_boundaries: List[float]
    ) -> List[List[Tuple[int, int, int, int]]]:
        """Assign bounding boxes to columns.
        
        Args:
            bboxes: Bounding boxes to assign
            column_boundaries: Column boundary x-coordinates
            
        Returns:
            List of columns, each containing bounding boxes
        """
        if not column_boundaries:
            return []
        
        num_columns = len(column_boundaries) - 1
        columns = [[] for _ in range(num_columns)]
        
        for bbox in bboxes:
            # Find which column this bbox belongs to
            x_center = (bbox[0] + bbox[2]) / 2
            
            for col_idx in range(num_columns):
                if column_boundaries[col_idx] <= x_center < column_boundaries[col_idx + 1]:
                    columns[col_idx].append(bbox)
                    break
        
        return columns
    
    @staticmethod
    def detect_column_count(image: np.ndarray, expected_columns: int = 4) -> int:
        """Estimate number of columns in table.
        
        Args:
            image: Input image
            expected_columns: Expected column count (for validation)
            
        Returns:
            Estimated column count
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Detect vertical lines
        _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        
        # Count vertical lines (rough estimate)
        contours, _ = cv2.findContours(vertical_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        significant_lines = [c for c in contours if cv2.boundingRect(c)[3] > 50]
        col_count = max(len(significant_lines) - 1, expected_columns)  # -1 because edges
        
        logger.debug(f"Detected {col_count} columns")
        return col_count
    
    @classmethod
    def organize_by_columns(
        cls,
        rows: List[List[Tuple[int, int, int, int]]],
        expected_columns: int = 4
    ) -> List[List[List[Tuple[int, int, int, int]]]]:
        """Organize rows into column structure.
        
        Args:
            rows: Rows of bounding boxes
            expected_columns: Expected number of columns
            
        Returns:
            2D structure: columns[col_idx][row_idx][bbox]
        """
        if not rows:
            return []
        
        # Extract column boundaries from all rows
        all_bboxes = []
        for row in rows:
            all_bboxes.extend(row)
        
        boundaries = cls.extract_column_boundaries(all_bboxes)
        if len(boundaries) < 2:
            # Fallback: estimate boundaries
            image_width = max(bbox[2] for bbox in all_bboxes)
            boundaries = [i * image_width / expected_columns for i in range(expected_columns + 1)]
        
        # Organize each row into columns
        columns = []
        for row in rows:
            columns_in_row = cls.assign_to_columns(row, boundaries)
            columns.append(columns_in_row)
        
        logger.debug(f"Organized {len(rows)} rows into {len(boundaries)-1} columns")
        return columns
