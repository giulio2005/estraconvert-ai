"""
Excel processing service
Handles Excel (.xlsx, .xls) to CSV conversion with AI-powered header detection
Fast and efficient for structured data
"""
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
from io import BytesIO

logger = logging.getLogger(__name__)


class ExcelService:
    """Service for processing Excel files"""

    def __init__(self):
        self.supported_extensions = ['.xlsx', '.xls', '.xlsm']

    def is_excel_file(self, filename: str) -> bool:
        """Check if file is an Excel file"""
        return any(filename.lower().endswith(ext) for ext in self.supported_extensions)

    def detect_header_row_with_ai(self, file_path: Path, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Use AI to detect which row contains the actual column headers and column types
        Returns dict with header_row (int) and columns (list of {name, type})
        """
        try:
            # Read first 20 rows without interpreting header
            df_preview = pd.read_excel(file_path, sheet_name=sheet_name or 0, header=None, nrows=20)

            # Convert preview to text representation for AI
            preview_text = "EXCEL FILE PREVIEW (First 20 rows):\n\n"
            for idx, row in df_preview.iterrows():
                row_values = [str(v) if pd.notna(v) else '' for v in row.values]
                preview_text += f"Row {idx}: {' | '.join(row_values)}\n"

            # Use AI service to detect header row
            from app.services.ai_service import AIService
            ai_service = AIService()

            prompt = f"""Analyze this Excel file preview and determine:
1. Which row number contains the actual column headers
2. The data type of each column (currency/number/date/text)

{preview_text}

IMPORTANT:
- Some Excel files have metadata rows at the top (company name, account info, etc.)
- The header row typically contains column names that describe the data
- Classify columns as:
  * "currency": monetary amounts (prices, debits, credits, balances, totals)
  * "number": non-monetary numbers (IDs, quantities, counts)
  * "date": dates or timestamps
  * "text": all other text data

Return ONLY a JSON object with this structure:
{{
  "header_row": <number>,
  "reasoning": "<brief explanation>",
  "columns": [
    {{"name": "column1", "type": "date"}},
    {{"name": "column2", "type": "text"}},
    {{"name": "column3", "type": "currency"}},
    ...
  ]
}}

Example response:
{{
  "header_row": 9,
  "reasoning": "Rows 0-8 contain metadata. Row 9 contains headers: 'Data Contabile', 'Data Valuta', 'Dare', 'Avere'",
  "columns": [
    {{"name": "Data Contabile", "type": "date"}},
    {{"name": "Data Valuta", "type": "date"}},
    {{"name": "Dare", "type": "currency"}},
    {{"name": "Avere", "type": "currency"}},
    {{"name": "Descrizioni Aggiuntive", "type": "text"}}
  ]
}}"""

            response = ai_service.ai_provider.generate_text(prompt, temperature=0, max_tokens=1000)

            # Parse AI response
            import json
            import re

            logger.info(f"🤖 AI response: {response[:200]}...")

            # Extract JSON from response (AI might add explanatory text)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                header_row = result.get('header_row', 0)
                columns = result.get('columns', [])
                logger.info(f"🤖 AI detected header at row {header_row}: {result.get('reasoning', '')}")
                logger.info(f"🤖 AI detected {len(columns)} columns with types")
                return {
                    'header_row': header_row,
                    'columns': columns  # [{name, type}, ...]
                }
            else:
                logger.warning("⚠️ AI response didn't contain valid JSON, using row 0")
                return {'header_row': 0, 'columns': []}

        except Exception as e:
            logger.error(f"❌ Error in AI header detection: {e}, falling back to row 0")
            return {'header_row': 0, 'columns': []}

    def read_excel_file(self, file_path: Path, sheet_name: Optional[str] = None, use_ai_detection: bool = True) -> pd.DataFrame:
        """
        Read Excel file into pandas DataFrame with AI-powered header detection

        Args:
            file_path: Path to Excel file
            sheet_name: Optional sheet name to read (default: first sheet)
            use_ai_detection: Use AI to detect header row (default: True)

        Returns:
            DataFrame with Excel data
        """
        try:
            # First, try AI detection to find the real header row
            header_row = 0
            if use_ai_detection:
                ai_result = self.detect_header_row_with_ai(file_path, sheet_name)
                header_row = ai_result.get('header_row', 0)

            # Read Excel file with correct header row
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
            else:
                df = pd.read_excel(file_path, sheet_name=0, header=header_row)  # First sheet

            logger.info(f"📊 Excel file read: {df.shape[0]} rows × {df.shape[1]} columns (header at row {header_row})")
            return df

        except Exception as e:
            logger.error(f"❌ Error reading Excel file: {e}")
            raise ValueError(f"Failed to read Excel file: {str(e)}")

    def get_sheet_names(self, file_path: Path) -> List[str]:
        """Get all sheet names from Excel file"""
        try:
            xls = pd.ExcelFile(file_path)
            return xls.sheet_names
        except Exception as e:
            logger.error(f"❌ Error getting sheet names: {e}")
            raise ValueError(f"Failed to read Excel file: {str(e)}")

    def get_excel_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Get information about Excel file structure

        Returns:
            Dict with sheets, columns, rows info
        """
        try:
            sheet_names = self.get_sheet_names(file_path)
            sheets_info = []

            for sheet_name in sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                sheets_info.append({
                    "name": sheet_name,
                    "rows": len(df),
                    "columns": list(df.columns),
                    "column_count": len(df.columns)
                })

            return {
                "sheet_count": len(sheet_names),
                "sheets": sheets_info
            }

        except Exception as e:
            logger.error(f"❌ Error getting Excel info: {e}")
            raise ValueError(f"Failed to analyze Excel file: {str(e)}")

    def detect_columns(self, file_path: Path, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Detect columns in Excel file with AI-powered column type detection

        Returns:
            Dict with detected columns and preview data
        """
        try:
            # Get AI detection results with column types (single AI call)
            ai_result = self.detect_header_row_with_ai(file_path, sheet_name)
            ai_columns = ai_result.get('columns', [])
            header_row = ai_result.get('header_row', 0)

            logger.info(f"📊 AI detected {len(ai_columns)} columns with types")

            # Create mapping from column name to AI-detected type
            ai_type_map = {col['name']: col['type'] for col in ai_columns}

            # Read Excel file with the detected header row (skip AI detection since we already have it)
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
            else:
                df = pd.read_excel(file_path, sheet_name=0, header=header_row)

            # Get column info
            columns = []
            for col in df.columns:
                col_name = str(col)

                # Use AI-detected type if available, otherwise fall back to pandas dtype
                if col_name in ai_type_map:
                    column_type = ai_type_map[col_name]
                    logger.info(f"   Column '{col_name}': {column_type} (AI-detected)")
                else:
                    # Fallback to pandas dtype if AI didn't detect this column
                    dtype = str(df[col].dtype)
                    if 'int' in dtype or 'float' in dtype:
                        column_type = 'number'
                    elif 'datetime' in dtype:
                        column_type = 'date'
                    else:
                        column_type = 'text'
                    logger.warning(f"   Column '{col_name}': {column_type} (fallback from {dtype})")

                # Get sample values (first 3 non-null)
                sample_values = df[col].dropna().head(3).tolist()

                columns.append({
                    "name": col_name,
                    "type": column_type,  # Use AI-detected type (currency/number/date/text)
                    "sample_values": [str(v) for v in sample_values]
                })

            # Get preview rows
            preview_data = df.head(5).to_dict('records')

            return {
                "columns": columns,
                "total_rows": len(df),
                "preview_data": preview_data,
                "sheet_name": sheet_name or "Sheet1"
            }

        except Exception as e:
            logger.error(f"❌ Error detecting columns: {e}")
            raise ValueError(f"Failed to detect columns: {str(e)}")

    def convert_to_csv(
        self,
        file_path: Path,
        selected_columns: Optional[List[str]] = None,
        sheet_name: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Convert Excel to CSV

        Args:
            file_path: Path to Excel file
            selected_columns: Optional list of columns to include
            sheet_name: Optional sheet name
            output_path: Optional output path (default: same name with .csv)

        Returns:
            Path to generated CSV file
        """
        try:
            # Read Excel
            df = self.read_excel_file(file_path, sheet_name)

            # Filter columns if specified
            if selected_columns:
                df = df[selected_columns]

            # Generate output path if not provided
            if not output_path:
                output_path = file_path.parent / f"{file_path.stem}.csv"

            # Convert to CSV
            df.to_csv(output_path, index=False, encoding='utf-8')

            logger.info(f"✅ CSV generated: {output_path} ({len(df)} rows)")
            return output_path

        except Exception as e:
            logger.error(f"❌ Error converting to CSV: {e}")
            raise ValueError(f"Failed to convert to CSV: {str(e)}")

    def clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean column names (remove spaces, special chars)
        Optional enhancement - can be enabled via user setting
        """
        df.columns = df.columns.str.strip()  # Remove leading/trailing spaces
        df.columns = df.columns.str.replace(' ', '_')  # Replace spaces with underscore
        df.columns = df.columns.str.lower()  # Lowercase
        return df


# Global service instance
excel_service = ExcelService()
