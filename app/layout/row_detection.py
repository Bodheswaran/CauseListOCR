"""
Row detection for cause list tables
Identifies horizontal text regions and groups them into logical rows
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class RowDetector:
    """Detect and extract table rows from images."""
    
    @staticmethod
    def detect_horizontal_lines(image: np.ndarray, threshold: int = 100) -> List[Tuple[int, int, int, int]]:
        """Detect horizontal lines in image.
        
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
        
        # Detect horizontal lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        lines = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 50:  # Minimum line width
                lines.append((x, y, x + w, y + h))
        
        return sorted(lines, key=lambda l: l[1])  # Sort by y coordinate
    
    @staticmethod
    def detect_text_regions(regions_from_ocr: List[Dict]) -> List[Tuple[int, int, int, int]]:
        """Extract bounding boxes from OCR regions.
        
        Args:
            regions_from_ocr: List of OCR text regions with bounding boxes
            
        Returns:
            List of bounding boxes as (x_min, y_min, x_max, y_max)
        """
        bboxes = []
        for region in regions_from_ocr:
            if 'bounding_box' in region:
                points = region['bounding_box']
                x_coords = [p[0] for p in points]
                y_coords = [p[1] for p in points]
                bbox = (
                    int(min(x_coords)),
                    int(min(y_coords)),
                    int(max(x_coords)),
                    int(max(y_coords))
                )
                bboxes.append(bbox)
        return bboxes
    
    @staticmethod
    def cluster_into_rows(
        bboxes: List[Tuple[int, int, int, int]],
        vertical_threshold: int = 20
    ) -> List[List[Tuple[int, int, int, int]]]:
        """Cluster bounding boxes into horizontal rows.
        
        Args:
            bboxes: List of bounding boxes (x_min, y_min, x_max, y_max)
            vertical_threshold: Maximum vertical gap to merge rows
            
        Returns:
            List of rows, each containing multiple bboxes
        """
        if not bboxes:
            return []
        
        # Sort by y coordinate
        sorted_bboxes = sorted(bboxes, key=lambda b: b[1])
        
        rows = []
        current_row = [sorted_bboxes[0]]
        current_y_max = sorted_bboxes[0][3]
        
        for bbox in sorted_bboxes[1:]:
            y_min = bbox[1]
            
            # Check if bbox belongs to current row
            if y_min - current_y_max <= vertical_threshold:
                current_row.append(bbox)
                current_y_max = max(current_y_max, bbox[3])
            else:
                # Start new row
                rows.append(current_row)
                current_row = [bbox]
                current_y_max = bbox[3]
        
        if current_row:
            rows.append(current_row)
        
        return rows
    
    @staticmethod
    def sort_row_items(row: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """Sort items in a row from left to right.
        
        Args:
            row: Bounding boxes in a row
            
        Returns:
            Sorted bounding boxes (left to right)
        """
        return sorted(row, key=lambda b: b[0])
    
    @classmethod
    def extract_rows_from_regions(
        cls,
        regions_from_ocr: List[Dict],
        vertical_threshold: int = 20
    ) -> List[List[Dict]]:
        """Extract and organize OCR regions into rows.
        
        Args:
            regions_from_ocr: OCR detected regions
            vertical_threshold: Gap threshold for row clustering
            
        Returns:
            List of rows, each containing OCR regions
        """
        # Get bounding boxes
        bboxes = cls.detect_text_regions(regions_from_ocr)
        if not bboxes:
            return []
        
        # Create mapping from bbox to region
        bbox_to_region = {}
        for i, region in enumerate(regions_from_ocr):
            if 'bounding_box' in region:
                points = region['bounding_box']
                x_coords = [p[0] for p in points]
                y_coords = [p[1] for p in points]
                bbox = (
                    int(min(x_coords)),
                    int(min(y_coords)),
                    int(max(x_coords)),
                    int(max(y_coords))
                )
                bbox_to_region[bbox] = region
        
        # Cluster into rows
        row_clusters = cls.cluster_into_rows(bboxes, vertical_threshold)
        
        # Convert back to regions
        rows = []
        for row_cluster in row_clusters:
            sorted_row = cls.sort_row_items(row_cluster)
            row_regions = [bbox_to_region[bbox] for bbox in sorted_row if bbox in bbox_to_region]
            rows.append(row_regions)
        
        logger.debug(f"Extracted {len(rows)} rows from OCR regions")
        return rows
