import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from app.config import settings
from app.models.schemas import DetectedColumn, ColumnType, SelectedColumn, FormatConfig
from app.services.ai_provider import get_ai_provider
from app.services.prompt_templates import PromptTemplates, Language, BankType
from app.services.data_validator import DataValidator
from app.services.quality_checker import QualityChecker, QualityMetrics
from app.services.cache_manager import get_cache_manager


class AIService:
    """Service for AI-powered document analysis with advanced prompt engineering and validation"""

    def __init__(self):
        self.ai_provider = get_ai_provider()
        self.prompt_templates = PromptTemplates()
        self.data_validator = DataValidator()
        self.quality_checker = QualityChecker()
        self.cache_manager = get_cache_manager()

    def _compute_doc_hash(self, text: str) -> str:
        """Compute SHA256 hash of document text for cache keys"""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def detect_columns(
        self,
        document_text: str,
        document_id: Optional[str] = None,
        language: Optional[Language] = None,
        bank_type: Optional[BankType] = None
    ) -> List[DetectedColumn]:
        """
        Analyze document text and detect table columns using advanced prompt templates.
        Auto-detects language and bank type for optimized extraction.
        FASE 4: Now with column detection caching.

        Args:
            document_text: Full document text
            document_id: Document ID for caching (optional)
            language: Optional language override (auto-detected if None)
            bank_type: Optional bank type override (auto-detected if None)

        Returns:
            List of detected columns with confidence scores
        """
        if not document_text:
            raise ValueError("No document text provided")

        # FASE 4: Check cache if document_id provided
        if document_id:
            doc_hash = self._compute_doc_hash(document_text)
            cached_columns = self.cache_manager.get_cached_columns(document_id, doc_hash)

            if cached_columns:
                print(f"✅ Cache hit: Column detection (skipping AI call)")
                # Convert cached dicts to DetectedColumn objects
                columns = []
                for col_data in cached_columns:
                    column = DetectedColumn(
                        id=col_data["id"],
                        name=col_data["name"],
                        type=ColumnType(col_data["type"]),
                        confidence=col_data.get("confidence", 0.9),
                    )
                    columns.append(column)
                return columns

        # Build adaptive prompt using template system
        prompt = self.prompt_templates.build_column_detection_prompt(
            document_text=document_text,
            language=language,
            bank_type=bank_type
        )

        # Detect context for logging
        detected_lang = language or self.prompt_templates.detect_language(document_text)
        detected_bank = bank_type or self.prompt_templates.detect_bank_type(document_text)

        print(f"\n{'='*80}")
        print(f"🌍 LANGUAGE: {detected_lang.value.upper()}")
        print(f"🏦 BANK TYPE: {detected_bank.value.upper()}")
        print(f"{'='*80}\n")

        try:
            # Generate content with AI provider
            content = self.ai_provider.generate_text(prompt, temperature=0, max_tokens=2000)

            # Log raw response for debugging
            print(f"RAW AI RESPONSE:")
            print(content[:500] + "..." if len(content) > 500 else content)
            print(f"{'='*80}\n")

            # Clean the response (remove markdown code blocks if present)
            content = self._clean_json_response(content)

            columns_data = json.loads(content)

            print(f"✅ PARSED COLUMNS: {len(columns_data)} columns detected")
            for col in columns_data:
                print(f"  - {col['name']} ({col['type']}) [confidence: {col.get('confidence', 0.9):.2f}]")

            # Convert to DetectedColumn objects
            columns = []
            for idx, col_data in enumerate(columns_data):
                column = DetectedColumn(
                    id=str(idx + 1),
                    name=col_data["name"],
                    type=ColumnType(col_data["type"]),
                    confidence=col_data.get("confidence", 0.9),
                )
                columns.append(column)

            # FASE 4: Cache columns if document_id provided
            if document_id:
                doc_hash = self._compute_doc_hash(document_text)
                # Convert columns to dict for caching
                columns_dict = [
                    {
                        "id": col.id,
                        "name": col.name,
                        "type": col.type.value,
                        "confidence": col.confidence
                    }
                    for col in columns
                ]
                self.cache_manager.cache_columns(document_id, doc_hash, columns_dict)

            return columns

        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse AI response as JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"Error in AI column detection: {str(e)}")

    def extract_table_data(
        self,
        document_text: str,
        selected_columns: List[SelectedColumn],
        format_config: FormatConfig,
        document_id: Optional[str] = None,
        language: Optional[Language] = None,
        enable_validation: bool = True,
    ) -> Tuple[List[List[str]], Optional[Dict[str, Any]]]:
        """
        Extract table data from document text using advanced prompt templates.
        Analyzes all pages to extract complete transaction data with adaptive prompts.
        Includes validation and quality scoring.
        FASE 4: Now with full extraction caching.

        Args:
            document_text: Full document text
            selected_columns: List of columns to extract
            format_config: Format configuration for output
            document_id: Document ID for caching (optional)
            language: Optional language override (auto-detected if None)
            enable_validation: Enable validation and quality checks (default: True)

        Returns:
            Tuple of (extracted_rows, quality_report) where quality_report contains
            validation issues, quality metrics, and field confidence scores
        """
        if not document_text:
            raise ValueError("No document text provided")

        # FASE 4: Check cache if document_id provided
        if document_id:
            doc_hash = self._compute_doc_hash(document_text)
            requested_columns = [col.output_name for col in selected_columns]
            cached_extraction = self.cache_manager.get_cached_extraction(
                document_id, doc_hash, requested_columns
            )

            if cached_extraction:
                print(f"✅ Cache hit: Extraction data (skipping AI call)")
                return cached_extraction['data'], None  # Return cached data without quality report

        # Prepare column data for template
        selected_columns_dict = [
            {
                'output_name': col.output_name,
                'order': col.order,
                'type': col.type.value if hasattr(col.type, 'value') else col.type
            }
            for col in selected_columns
        ]

        # Prepare format config
        format_config_dict = {
            'delimiter': format_config.delimiter,
            'decimal_separator': format_config.decimal_separator,
            'thousands_separator': format_config.thousands_separator,
        }

        # Build adaptive prompt using template system
        prompt = self.prompt_templates.build_data_extraction_prompt(
            document_text=document_text,
            selected_columns=selected_columns_dict,
            format_config=format_config_dict,
            language=language
        )

        # Detect language for logging
        detected_lang = language or self.prompt_templates.detect_language(document_text)
        print(f"\n{'='*80}")
        print(f"🌍 EXTRACTION LANGUAGE: {detected_lang.value.upper()}")
        print(f"📊 COLUMNS: {len(selected_columns_dict)}")
        print(f"{'='*80}\n")

        try:
            # Generate content with AI provider (increased tokens for large documents)
            content = self.ai_provider.generate_text(prompt, temperature=0, max_tokens=32000)

            # Log raw response for debugging
            print(f"RAW AI DATA EXTRACTION RESPONSE:")
            print(content[:500] + "..." if len(content) > 500 else content)
            print(f"{'='*80}\n")

            # Clean the response
            content = self._clean_json_response(content)

            # Try to fix truncated JSON by finding the last complete entry
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parsing failed, attempting to fix truncated response...")
                print(f"Error: {str(e)}")
                data = self._fix_truncated_json(content)

            # Convert None/null values to empty strings and validate
            cleaned_data = self._clean_and_validate_data(data, len(selected_columns_dict))

            print(f"✅ EXTRACTED DATA: {len(cleaned_data)} rows")

            # FASE 2: Validation & Quality Checks
            quality_report = None
            if enable_validation:
                print(f"\n{'='*80}")
                print(f"🔍 RUNNING VALIDATION & QUALITY CHECKS")
                print(f"{'='*80}\n")

                # Step 1: Validate data schemas and formats
                validated_data, validation_issues = self.data_validator.validate_data(
                    cleaned_data,
                    selected_columns_dict
                )

                # Step 2: Quality checks and auto-corrections
                corrected_data, quality_metrics = self.quality_checker.check_quality(
                    validated_data,
                    selected_columns_dict
                )

                # Step 3: Calculate field-level confidence scores
                field_confidence = self.quality_checker.analyze_field_confidence(
                    corrected_data,
                    selected_columns_dict
                )

                # Build quality report
                quality_report = {
                    "validation": self.data_validator.get_validation_summary(),
                    "quality_metrics": quality_metrics.to_dict(),
                    "field_confidence": field_confidence,
                    "has_critical_errors": self.data_validator.has_critical_errors()
                }

                # Log summary
                print(f"📊 QUALITY REPORT:")
                print(f"  - Validation issues: {quality_report['validation']['total_issues']}")
                print(f"  - Quality score: {quality_metrics.quality_score:.1f}/100")
                print(f"  - Completeness: {quality_metrics.completeness_score:.1f}%")
                print(f"  - Confidence: {quality_metrics.confidence_score:.1f}%")
                print(f"  - Duplicates: {quality_metrics.duplicate_rows}")
                print(f"  - Chronology issues: {quality_metrics.chronology_issues}")
                print(f"\n📈 FIELD CONFIDENCE:")
                for field, conf in field_confidence.items():
                    print(f"  - {field}: {conf:.0%}")
                print(f"{'='*80}\n")

                # Use corrected data
                cleaned_data = corrected_data

            # FASE 4: Cache extraction if document_id provided
            if document_id:
                doc_hash = self._compute_doc_hash(document_text)
                column_names = [col.output_name for col in selected_columns]
                self.cache_manager.cache_extraction(
                    document_id, doc_hash, cleaned_data, column_names
                )

            return cleaned_data, quality_report

        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse AI response as JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"Error in AI data extraction: {str(e)}")

    def _clean_json_response(self, content: str) -> str:
        """
        Clean AI response to extract pure JSON

        Args:
            content: Raw AI response

        Returns:
            Cleaned JSON string
        """
        # Remove markdown code blocks
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        return content.strip()

    def _fix_truncated_json(self, content: str) -> List[List[str]]:
        """
        Attempt to fix truncated JSON responses

        Args:
            content: Potentially truncated JSON string

        Returns:
            Parsed data array

        Raises:
            json.JSONDecodeError if recovery fails
        """
        # Try to find last complete array entry
        last_complete_bracket = content.rfind(']],')
        if last_complete_bracket > 0:
            fixed_content = content[:last_complete_bracket + 2] + '\n]'
            print(f"🔧 Attempting to fix by truncating at position {last_complete_bracket}")
            data = json.loads(fixed_content)
            print(f"✓ Fixed! Recovered {len(data)} rows")
            return data

        # If that doesn't work, try to find last complete row
        last_bracket = content.rfind('],')
        if last_bracket > 0:
            fixed_content = content[:last_bracket + 1] + '\n]'
            data = json.loads(fixed_content)
            print(f"✓ Fixed! Recovered {len(data)} rows")
            return data

        # Can't fix, re-raise
        raise json.JSONDecodeError("Unable to fix truncated JSON", content, 0)

    def _clean_and_validate_data(
        self,
        data: List[List[Any]],
        expected_columns: int
    ) -> List[List[str]]:
        """
        Clean and validate extracted data

        Args:
            data: Raw extracted data
            expected_columns: Expected number of columns per row

        Returns:
            Cleaned and validated data
        """
        cleaned_data = []

        for row_idx, row in enumerate(data):
            # Convert None/null values to empty strings
            cleaned_row = []
            for cell in row:
                if cell is None or cell == "null":
                    cleaned_row.append("")
                else:
                    cleaned_row.append(str(cell))

            # Validate row length
            if len(cleaned_row) != expected_columns:
                print(f"⚠️  Row {row_idx + 1} has {len(cleaned_row)} columns, expected {expected_columns}")
                # Pad or truncate to match expected length
                if len(cleaned_row) < expected_columns:
                    cleaned_row.extend([""] * (expected_columns - len(cleaned_row)))
                else:
                    cleaned_row = cleaned_row[:expected_columns]

            cleaned_data.append(cleaned_row)

        return cleaned_data
