"""
Data Validator - Schema and format validation for extracted data
Ensures data quality and consistency before returning to user
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum


class ValidationLevel(str, Enum):
    """Validation severity levels"""
    ERROR = "error"      # Critical issue, data unusable
    WARNING = "warning"  # Issue that may need attention
    INFO = "info"        # Informational notice


class ValidationIssue:
    """Represents a validation issue found in data"""

    def __init__(
        self,
        level: ValidationLevel,
        row_index: int,
        column_index: int,
        field_name: str,
        message: str,
        value: str = "",
        suggestion: str = ""
    ):
        self.level = level
        self.row_index = row_index
        self.column_index = column_index
        self.field_name = field_name
        self.message = message
        self.value = value
        self.suggestion = suggestion

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "level": self.level.value,
            "row": self.row_index + 1,  # 1-indexed for user display
            "column": self.column_index + 1,
            "field": self.field_name,
            "message": self.message,
            "value": self.value,
            "suggestion": self.suggestion if self.suggestion else None
        }


class DataValidator:
    """Validates extracted data for quality and consistency"""

    # Common date formats for Italian bank statements
    DATE_FORMATS = [
        "%d/%m/%Y",      # 31/12/2025
        "%d-%m-%Y",      # 31-12-2025
        "%Y-%m-%d",      # 2025-12-31
        "%d/%m/%y",      # 31/12/25
        "%d.%m.%Y",      # 31.12.2025
        "%d %m %Y",      # 31 12 2025
        "%d/%m/%Y %H:%M",  # 31/12/2025 14:30
    ]

    # Regex patterns for validation
    AMOUNT_PATTERN = re.compile(r'^-?\d{1,3}(?:[.,\s]\d{3})*[.,]?\d{0,2}$')
    EMPTY_PATTERN = re.compile(r'^\s*$')

    def __init__(self):
        self.issues: List[ValidationIssue] = []

    def validate_data(
        self,
        data: List[List[str]],
        column_config: List[Dict[str, Any]]
    ) -> Tuple[List[List[str]], List[ValidationIssue]]:
        """
        Validate extracted data against column configuration

        Args:
            data: Extracted data rows
            column_config: Column configuration with types

        Returns:
            Tuple of (validated_data, issues_list)
        """
        self.issues = []
        validated_data = []

        for row_idx, row in enumerate(data):
            validated_row = []

            # Check row length matches expected columns
            if len(row) != len(column_config):
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    row_index=row_idx,
                    column_index=-1,
                    field_name="row",
                    message=f"Row has {len(row)} columns, expected {len(column_config)}",
                    value=str(row)
                ))
                # Pad or truncate to match expected length
                if len(row) < len(column_config):
                    row = row + [""] * (len(column_config) - len(row))
                else:
                    row = row[:len(column_config)]

            # Validate each cell
            for col_idx, (cell, col_config) in enumerate(zip(row, column_config)):
                validated_cell = self._validate_cell(
                    cell,
                    col_config,
                    row_idx,
                    col_idx
                )
                validated_row.append(validated_cell)

            validated_data.append(validated_row)

        return validated_data, self.issues

    def _validate_cell(
        self,
        value: str,
        column_config: Dict[str, Any],
        row_idx: int,
        col_idx: int
    ) -> str:
        """
        Validate individual cell based on column type

        Args:
            value: Cell value
            column_config: Column configuration
            row_idx: Row index
            col_idx: Column index

        Returns:
            Validated/corrected value
        """
        field_name = column_config.get('output_name', f'Column{col_idx}')
        field_type = column_config.get('type', 'text')

        # Handle empty values
        if self.EMPTY_PATTERN.match(value):
            # Empty is acceptable for optional fields
            if field_type in ['currency', 'number']:
                # Currency/number can be empty (e.g., debit OR credit column)
                return value.strip()
            elif field_type == 'date':
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    row_index=row_idx,
                    column_index=col_idx,
                    field_name=field_name,
                    message="Date field is empty",
                    value=value
                ))
                return value.strip()
            else:
                return value.strip()

        # Type-specific validation
        if field_type == 'date':
            return self._validate_date(value, field_name, row_idx, col_idx)
        elif field_type == 'currency':
            return self._validate_currency(value, field_name, row_idx, col_idx)
        elif field_type == 'number':
            return self._validate_number(value, field_name, row_idx, col_idx)
        else:  # text
            return self._validate_text(value, field_name, row_idx, col_idx)

    def _validate_date(
        self,
        value: str,
        field_name: str,
        row_idx: int,
        col_idx: int
    ) -> str:
        """Validate date format"""
        value = value.strip()

        # Try to parse with known formats
        for date_format in self.DATE_FORMATS:
            try:
                parsed_date = datetime.strptime(value, date_format)

                # Check if date is reasonable (not too far in past/future)
                current_year = datetime.now().year
                if parsed_date.year < 1900 or parsed_date.year > current_year + 10:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        row_index=row_idx,
                        column_index=col_idx,
                        field_name=field_name,
                        message=f"Date year ({parsed_date.year}) seems unusual",
                        value=value
                    ))

                return value  # Valid date

            except ValueError:
                continue

        # Date format not recognized
        self.issues.append(ValidationIssue(
            level=ValidationLevel.WARNING,
            row_index=row_idx,
            column_index=col_idx,
            field_name=field_name,
            message="Date format not recognized",
            value=value,
            suggestion="Expected format: DD/MM/YYYY"
        ))

        return value

    def _validate_currency(
        self,
        value: str,
        field_name: str,
        row_idx: int,
        col_idx: int
    ) -> str:
        """Validate currency/amount format"""
        value = value.strip()

        # Check if matches amount pattern
        if not self.AMOUNT_PATTERN.match(value):
            # Try to detect common issues
            if any(char.isalpha() for char in value):
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    row_index=row_idx,
                    column_index=col_idx,
                    field_name=field_name,
                    message="Amount contains letters",
                    value=value
                ))
            else:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    row_index=row_idx,
                    column_index=col_idx,
                    field_name=field_name,
                    message="Amount format may be incorrect",
                    value=value
                ))

        # Check for unreasonably large amounts (> 1 billion)
        try:
            # Normalize to parse: remove thousands separators, convert decimal
            normalized = value.replace('.', '').replace(',', '.').replace(' ', '')
            amount = float(normalized)
            if abs(amount) > 1_000_000_000:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    row_index=row_idx,
                    column_index=col_idx,
                    field_name=field_name,
                    message=f"Amount seems unusually large: {amount:,.2f}",
                    value=value
                ))
        except ValueError:
            pass  # Already flagged above

        return value

    def _validate_number(
        self,
        value: str,
        field_name: str,
        row_idx: int,
        col_idx: int
    ) -> str:
        """Validate numeric (non-currency) field"""
        value = value.strip()

        # Check if it's a valid number
        try:
            float(value.replace(',', '.'))
        except ValueError:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                row_index=row_idx,
                column_index=col_idx,
                field_name=field_name,
                message="Expected numeric value",
                value=value
            ))

        return value

    def _validate_text(
        self,
        value: str,
        field_name: str,
        row_idx: int,
        col_idx: int
    ) -> str:
        """Validate text field"""
        value = value.strip()

        # Check for suspiciously short descriptions
        if len(value) < 2 and value:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                row_index=row_idx,
                column_index=col_idx,
                field_name=field_name,
                message="Text field is very short",
                value=value
            ))

        # Check for unusual characters that might indicate OCR errors
        unusual_chars = re.findall(r'[^\w\s\-\.,/()€$£¥]', value)
        if unusual_chars:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                row_index=row_idx,
                column_index=col_idx,
                field_name=field_name,
                message=f"Contains unusual characters: {set(unusual_chars)}",
                value=value
            ))

        return value

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get summary of validation results

        Returns:
            Dictionary with validation statistics
        """
        errors = [i for i in self.issues if i.level == ValidationLevel.ERROR]
        warnings = [i for i in self.issues if i.level == ValidationLevel.WARNING]
        infos = [i for i in self.issues if i.level == ValidationLevel.INFO]

        return {
            "total_issues": len(self.issues),
            "errors": len(errors),
            "warnings": len(warnings),
            "infos": len(infos),
            "issues": [issue.to_dict() for issue in self.issues]
        }

    def has_critical_errors(self) -> bool:
        """Check if there are any critical errors"""
        return any(i.level == ValidationLevel.ERROR for i in self.issues)
