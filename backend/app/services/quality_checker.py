"""
Quality Checker - Business logic validation and data quality scoring
Checks chronological order, duplicates, completeness, and confidence
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import Counter


class QualityMetrics:
    """Container for quality metrics"""

    def __init__(self):
        self.total_rows = 0
        self.complete_rows = 0
        self.incomplete_rows = 0
        self.duplicate_rows = 0
        self.chronology_issues = 0
        self.completeness_score = 0.0
        self.confidence_score = 0.0
        self.quality_score = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_rows": self.total_rows,
            "complete_rows": self.complete_rows,
            "incomplete_rows": self.incomplete_rows,
            "duplicate_rows": self.duplicate_rows,
            "chronology_issues": self.chronology_issues,
            "completeness_score": round(self.completeness_score, 2),
            "confidence_score": round(self.confidence_score, 2),
            "quality_score": round(self.quality_score, 2)
        }


class QualityChecker:
    """Performs business logic checks and quality scoring"""

    # Common OCR errors to auto-correct
    OCR_CORRECTIONS = {
        'O': '0',  # Letter O → Zero
        'o': '0',
        'I': '1',  # Letter I → One
        'l': '1',
        'S': '5',  # Letter S → Five (in numeric context)
        'B': '8',  # Letter B → Eight (in numeric context)
    }

    def __init__(self):
        self.metrics = QualityMetrics()

    def check_quality(
        self,
        data: List[List[str]],
        column_config: List[Dict[str, Any]]
    ) -> Tuple[List[List[str]], QualityMetrics]:
        """
        Perform quality checks and auto-corrections

        Args:
            data: Extracted data rows
            column_config: Column configuration

        Returns:
            Tuple of (corrected_data, quality_metrics)
        """
        self.metrics = QualityMetrics()
        self.metrics.total_rows = len(data)

        corrected_data = []

        # Find date column indices
        date_columns = [
            i for i, col in enumerate(column_config)
            if col.get('type') == 'date'
        ]

        # Find amount column indices
        amount_columns = [
            i for i, col in enumerate(column_config)
            if col.get('type') in ['currency', 'number']
        ]

        for row_idx, row in enumerate(data):
            # Auto-correct OCR errors
            corrected_row = self._auto_correct_row(row, amount_columns)

            # Check completeness
            if self._is_row_complete(corrected_row):
                self.metrics.complete_rows += 1
            else:
                self.metrics.incomplete_rows += 1

            corrected_data.append(corrected_row)

        # Check for duplicates
        self.metrics.duplicate_rows = self._count_duplicates(corrected_data)

        # Check chronological order (if date columns exist)
        if date_columns:
            self.metrics.chronology_issues = self._check_chronology(
                corrected_data,
                date_columns[0]
            )

        # Calculate scores
        self._calculate_scores()

        return corrected_data, self.metrics

    def _auto_correct_row(
        self,
        row: List[str],
        amount_columns: List[int]
    ) -> List[str]:
        """
        Auto-correct common OCR errors in row

        Args:
            row: Data row
            amount_columns: Indices of amount columns

        Returns:
            Corrected row
        """
        corrected_row = []

        for col_idx, cell in enumerate(row):
            if col_idx in amount_columns:
                # Correct OCR errors in amounts
                corrected = self._correct_amount(cell)
            else:
                corrected = cell

            corrected_row.append(corrected)

        return corrected_row

    def _correct_amount(self, value: str) -> str:
        """
        Correct common OCR errors in amount values

        Args:
            value: Amount string

        Returns:
            Corrected amount
        """
        if not value or value.strip() == "":
            return value

        corrected = value.strip()

        # Simple approach: detect if value looks like an amount (has digits and separators)
        # Then replace common OCR mistakes
        has_digits = any(c.isdigit() for c in corrected)
        has_separators = any(c in ',.;' for c in corrected)

        if has_digits or has_separators:
            # Replace letter O with zero (most common OCR error in amounts)
            corrected = corrected.replace('O', '0').replace('o', '0')
            # Replace letter I/l with one
            corrected = corrected.replace('I', '1').replace('l', '1')
            # Less common: S→5, B→8 only if surrounded by digits
            if re.search(r'\dS\d', corrected):
                corrected = corrected.replace('S', '5')
            if re.search(r'\dB\d', corrected):
                corrected = corrected.replace('B', '8')

        return corrected

    def _is_row_complete(self, row: List[str]) -> bool:
        """
        Check if row is complete (no excessive empty cells)

        Args:
            row: Data row

        Returns:
            True if row is considered complete
        """
        non_empty = sum(1 for cell in row if cell.strip())
        # Consider complete if at least 70% of cells are filled
        return non_empty >= len(row) * 0.7

    def _count_duplicates(self, data: List[List[str]]) -> int:
        """
        Count duplicate rows

        Args:
            data: All data rows

        Returns:
            Number of duplicate rows
        """
        # Convert rows to tuples for hashing
        row_tuples = [tuple(row) for row in data]
        counts = Counter(row_tuples)

        # Count rows that appear more than once
        duplicates = sum(count - 1 for count in counts.values() if count > 1)
        return duplicates

    def _check_chronology(
        self,
        data: List[List[str]],
        date_column_idx: int
    ) -> int:
        """
        Check if dates are in chronological order

        Args:
            data: All data rows
            date_column_idx: Index of date column

        Returns:
            Number of chronology violations
        """
        issues = 0
        previous_date = None

        date_formats = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%d/%m/%y",
            "%d.%m.%Y",
        ]

        for row in data:
            if date_column_idx >= len(row):
                continue

            date_str = row[date_column_idx].strip()
            if not date_str:
                continue

            # Try to parse date
            parsed_date = None
            for date_format in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, date_format)
                    break
                except ValueError:
                    continue

            if parsed_date and previous_date:
                # Check if date goes backwards (allowing same date)
                if parsed_date < previous_date:
                    issues += 1

            if parsed_date:
                previous_date = parsed_date

        return issues

    def _calculate_scores(self):
        """Calculate overall quality scores"""
        if self.metrics.total_rows == 0:
            return

        # Completeness score (0-100)
        self.metrics.completeness_score = (
            self.metrics.complete_rows / self.metrics.total_rows
        ) * 100

        # Confidence score based on multiple factors (0-100)
        duplicate_penalty = min(self.metrics.duplicate_rows * 5, 30)
        chronology_penalty = min(self.metrics.chronology_issues * 10, 30)
        incomplete_penalty = (
            self.metrics.incomplete_rows / self.metrics.total_rows
        ) * 40

        self.metrics.confidence_score = max(
            0,
            100 - duplicate_penalty - chronology_penalty - incomplete_penalty
        )

        # Overall quality score (average of completeness and confidence)
        self.metrics.quality_score = (
            self.metrics.completeness_score + self.metrics.confidence_score
        ) / 2

    def analyze_field_confidence(
        self,
        data: List[List[str]],
        column_config: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate confidence score for each field/column

        Args:
            data: Extracted data
            column_config: Column configuration

        Returns:
            Dictionary mapping field names to confidence scores (0-1)
        """
        field_scores = {}

        for col_idx, col_config in enumerate(column_config):
            field_name = col_config.get('output_name', f'Column{col_idx}')
            field_type = col_config.get('type', 'text')

            # Extract column values
            column_values = [
                row[col_idx] if col_idx < len(row) else ""
                for row in data
            ]

            # Calculate confidence based on completeness and format
            non_empty = sum(1 for v in column_values if v.strip())
            completeness_ratio = non_empty / len(column_values) if column_values else 0

            # Type-specific confidence adjustments
            format_score = 1.0
            if field_type == 'date':
                format_score = self._check_date_format_consistency(column_values)
            elif field_type in ['currency', 'number']:
                format_score = self._check_number_format_consistency(column_values)

            # Combined confidence (60% completeness, 40% format consistency)
            confidence = (completeness_ratio * 0.6) + (format_score * 0.4)
            field_scores[field_name] = round(confidence, 2)

        return field_scores

    def _check_date_format_consistency(self, values: List[str]) -> float:
        """Check if dates follow consistent format"""
        if not values:
            return 0.0

        date_formats = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%d/%m/%y",
            "%d.%m.%Y",
        ]

        valid_count = 0
        for value in values:
            if not value.strip():
                continue

            for date_format in date_formats:
                try:
                    datetime.strptime(value.strip(), date_format)
                    valid_count += 1
                    break
                except ValueError:
                    continue

        non_empty = sum(1 for v in values if v.strip())
        return valid_count / non_empty if non_empty > 0 else 0.0

    def _check_number_format_consistency(self, values: List[str]) -> float:
        """Check if numbers follow consistent format"""
        if not values:
            return 0.0

        amount_pattern = re.compile(r'^-?\d{1,3}(?:[.,\s]\d{3})*[.,]?\d{0,2}$')
        valid_count = 0

        for value in values:
            if not value.strip():
                continue

            if amount_pattern.match(value.strip()):
                valid_count += 1

        non_empty = sum(1 for v in values if v.strip())
        return valid_count / non_empty if non_empty > 0 else 0.0
