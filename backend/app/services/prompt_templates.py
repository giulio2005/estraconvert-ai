"""
Advanced prompt templates for AI-powered document analysis
Supports multi-language, bank-specific patterns, and adaptive detection
"""
from typing import List, Dict, Any, Optional
from enum import Enum


class Language(str, Enum):
    """Supported languages"""
    IT = "it"
    EN = "en"
    AUTO = "auto"


class BankType(str, Enum):
    """Known bank types with specific patterns"""
    GENERIC = "generic"
    INTESA_SANPAOLO = "intesa"
    UNICREDIT = "unicredit"
    BNL = "bnl"
    MONTE_PASCHI = "mps"
    BANCO_BPM = "bpm"


# Bank-specific column patterns
BANK_PATTERNS = {
    BankType.INTESA_SANPAOLO: {
        "date_columns": ["Data Contabile", "Data Valuta", "Data"],
        "amount_columns": ["Dare", "Avere", "Importo"],
        "description_columns": ["Descrizione", "Causale", "Dettagli"],
    },
    BankType.UNICREDIT: {
        "date_columns": ["Data Operazione", "Data Valuta", "Data"],
        "amount_columns": ["Addebiti", "Accrediti", "Importo"],
        "description_columns": ["Descrizione Operazione", "Causale"],
    },
    BankType.BNL: {
        "date_columns": ["Data", "Data Contabile", "Data Valuta"],
        "amount_columns": ["Dare", "Avere", "Importo"],
        "description_columns": ["Descrizione", "Operazione"],
    },
    BankType.GENERIC: {
        "date_columns": ["Data", "Date", "Data Contabile", "Data Valuta", "Data Operazione"],
        "amount_columns": ["Importo", "Amount", "Dare", "Avere", "Debit", "Credit", "Addebiti", "Accrediti"],
        "description_columns": ["Descrizione", "Description", "Causale", "Dettagli", "Details"],
    },
}


# Multi-language keywords for filtering
FILTER_KEYWORDS = {
    Language.IT: {
        "skip_rows": ["SALDO", "TOTALE", "TOTALI", "RIEPILOGO", "SOMMARIO", "CHIUSURA", "APERTURA"],
        "balance_terms": ["SALDO INIZIALE", "SALDO FINALE", "SALDO CONTABILE", "SALDO DISPONIBILE"],
        "summary_terms": ["TOTALE DARE", "TOTALE AVERE", "TOTALE MOVIMENTI"],
    },
    Language.EN: {
        "skip_rows": ["BALANCE", "TOTAL", "TOTALS", "SUMMARY", "CLOSING", "OPENING"],
        "balance_terms": ["OPENING BALANCE", "CLOSING BALANCE", "CURRENT BALANCE", "AVAILABLE BALANCE"],
        "summary_terms": ["TOTAL DEBIT", "TOTAL CREDIT", "TOTAL TRANSACTIONS"],
    },
}


# Few-shot examples for better accuracy
FEW_SHOT_EXAMPLES = {
    "column_detection_it": [
        {
            "input": "Data Contabile | Data Valuta | Descrizione | Dare | Avere",
            "output": [
                {"name": "Data Contabile", "type": "date", "confidence": 0.95},
                {"name": "Data Valuta", "type": "date", "confidence": 0.95},
                {"name": "Descrizione", "type": "text", "confidence": 0.98},
                {"name": "Dare", "type": "currency", "confidence": 0.97},
                {"name": "Avere", "type": "currency", "confidence": 0.97},
            ]
        },
        {
            "input": "Data Operazione | Causale | Importo | Saldo",
            "output": [
                {"name": "Data Operazione", "type": "date", "confidence": 0.95},
                {"name": "Causale", "type": "text", "confidence": 0.98},
                {"name": "Importo", "type": "currency", "confidence": 0.97},
            ]
        },
    ],
    "column_detection_en": [
        {
            "input": "Date | Description | Debit | Credit | Balance",
            "output": [
                {"name": "Date", "type": "date", "confidence": 0.95},
                {"name": "Description", "type": "text", "confidence": 0.98},
                {"name": "Debit", "type": "currency", "confidence": 0.97},
                {"name": "Credit", "type": "currency", "confidence": 0.97},
            ]
        },
    ],
}


class PromptTemplates:
    """Centralized prompt templates with multi-language and bank-specific support"""

    @staticmethod
    def detect_language(text: str) -> Language:
        """
        Auto-detect document language from text sample

        Args:
            text: Document text sample (first 500 chars usually enough)

        Returns:
            Detected language
        """
        text_lower = text.lower()

        # Count Italian keywords
        it_keywords = ["data", "contabile", "valuta", "importo", "dare", "avere", "descrizione", "causale"]
        it_score = sum(1 for keyword in it_keywords if keyword in text_lower)

        # Count English keywords
        en_keywords = ["date", "amount", "debit", "credit", "description", "balance", "transaction"]
        en_score = sum(1 for keyword in en_keywords if keyword in text_lower)

        return Language.IT if it_score > en_score else Language.EN

    @staticmethod
    def detect_bank_type(text: str) -> BankType:
        """
        Detect bank type from document text

        Args:
            text: Document text

        Returns:
            Detected bank type or GENERIC
        """
        text_lower = text.lower()

        if "intesa" in text_lower or "sanpaolo" in text_lower:
            return BankType.INTESA_SANPAOLO
        elif "unicredit" in text_lower:
            return BankType.UNICREDIT
        elif "bnl" in text_lower or "banca nazionale del lavoro" in text_lower:
            return BankType.BNL
        elif "monte paschi" in text_lower or "mps" in text_lower:
            return BankType.MONTE_PASCHI
        elif "banco bpm" in text_lower:
            return BankType.BANCO_BPM

        return BankType.GENERIC

    @staticmethod
    def build_column_detection_prompt(
        document_text: str,
        language: Optional[Language] = None,
        bank_type: Optional[BankType] = None,
    ) -> str:
        """
        Build adaptive column detection prompt with context

        Args:
            document_text: Full document text
            language: Optional language (auto-detected if None)
            bank_type: Optional bank type (auto-detected if None)

        Returns:
            Optimized prompt for column detection
        """
        # Auto-detect if not provided
        if language is None or language == Language.AUTO:
            language = PromptTemplates.detect_language(document_text)

        if bank_type is None:
            bank_type = PromptTemplates.detect_bank_type(document_text)

        # Get bank-specific patterns
        patterns = BANK_PATTERNS.get(bank_type, BANK_PATTERNS[BankType.GENERIC])

        # Get language-specific keywords
        keywords = FILTER_KEYWORDS.get(language, FILTER_KEYWORDS[Language.EN])

        # Build examples section
        examples_key = f"column_detection_{language.value}"
        examples = FEW_SHOT_EXAMPLES.get(examples_key, FEW_SHOT_EXAMPLES["column_detection_en"])

        examples_text = "\n\nEXAMPLES:\n"
        for i, example in enumerate(examples, 1):
            examples_text += f"\nExample {i}:\n"
            examples_text += f"Input: {example['input']}\n"
            examples_text += f"Output: {example['output']}\n"

        # Build main prompt
        if language == Language.IT:
            prompt = f"""Analizza questo estratto conto e identifica le colonne della tabella movimenti.

TESTO DOCUMENTO:
{document_text}

COLONNE TIPICHE DA CERCARE:
- Date: {', '.join(patterns['date_columns'])}
- Importi: {', '.join(patterns['amount_columns'])}
- Descrizioni: {', '.join(patterns['description_columns'])}

REGOLE IMPORTANTI:
1. Cerca SOLO intestazioni della tabella movimenti (non totali, saldi, o intestazioni di riepilogo)
2. Ignora righe con: {', '.join(keywords['skip_rows'])}
3. Ignora: {', '.join(keywords['balance_terms'])}
4. Classifica ogni colonna come:
   - "date": date o timestamp
   - "currency": importi monetari (dare, avere, addebiti, accrediti)
   - "number": numeri non monetari (ID, progressivi)
   - "text": testo descrittivo

FORMATO OUTPUT:
Ritorna SOLO un array JSON con questa struttura:
[
  {{"name": "nome_colonna", "type": "date|text|currency|number", "confidence": 0.0-1.0}}
]

Non includere colonne di saldo o totali.{examples_text}

Ora analizza il documento e ritorna SOLO il JSON array."""

        else:  # English
            prompt = f"""Analyze this bank statement and identify transaction table column headers.

DOCUMENT TEXT:
{document_text}

TYPICAL COLUMNS TO FIND:
- Dates: {', '.join(patterns['date_columns'])}
- Amounts: {', '.join(patterns['amount_columns'])}
- Descriptions: {', '.join(patterns['description_columns'])}

IMPORTANT RULES:
1. Find ONLY transaction table headers (not totals, balances, or summary headers)
2. Ignore rows with: {', '.join(keywords['skip_rows'])}
3. Ignore: {', '.join(keywords['balance_terms'])}
4. Classify each column as:
   - "date": dates or timestamps
   - "currency": monetary amounts (debit, credit)
   - "number": non-monetary numbers (IDs, counters)
   - "text": descriptive text

OUTPUT FORMAT:
Return ONLY a JSON array with this structure:
[
  {{"name": "column_name", "type": "date|text|currency|number", "confidence": 0.0-1.0}}
]

Do not include balance or total columns.{examples_text}

Now analyze the document and return ONLY the JSON array."""

        return prompt

    @staticmethod
    def build_data_extraction_prompt(
        document_text: str,
        selected_columns: List[Dict[str, Any]],
        format_config: Dict[str, Any],
        language: Optional[Language] = None,
    ) -> str:
        """
        Build adaptive data extraction prompt with format specifications

        Args:
            document_text: Full document text
            selected_columns: List of selected columns to extract
            format_config: Format configuration (separators, etc.)
            language: Optional language (auto-detected if None)

        Returns:
            Optimized prompt for data extraction
        """
        # Auto-detect language
        if language is None or language == Language.AUTO:
            language = PromptTemplates.detect_language(document_text)

        # Get filter keywords
        keywords = FILTER_KEYWORDS.get(language, FILTER_KEYWORDS[Language.EN])

        # Build column format
        column_names = [col['output_name'] for col in sorted(selected_columns, key=lambda x: x['order'])]
        column_order = format_config['delimiter'].join(column_names)

        # Build number format specifications
        decimal_sep = format_config['decimal_separator']
        thousand_sep = format_config.get('thousands_separator', 'none')

        if thousand_sep == 'none':
            thousand_sep = ''

        number_format_spec = f"- Separatore decimale: '{decimal_sep}'\n"
        if thousand_sep:
            number_format_spec += f"- Separatore migliaia: '{thousand_sep}'\n"
            number_format_spec += f"- Esempio: 1{thousand_sep}234{decimal_sep}56"
        else:
            number_format_spec += "- NO separatore migliaia\n"
            number_format_spec += f"- Esempio: 1234{decimal_sep}56"

        # Build conversion examples
        conversion_examples = ""
        if decimal_sep == ',' and thousand_sep == '.':
            conversion_examples = """
Esempi conversione:
- Documento: "2,500.00" → Output: "2.500,00"
- Documento: "85.50" → Output: "85,50"
- Documento: "1.234,56" → Output: "1.234,56" (già corretto)"""
        elif decimal_sep == '.' and thousand_sep == ',':
            conversion_examples = """
Conversion examples:
- Document: "1.234,56" → Output: "1,234.56"
- Document: "85,50" → Output: "85.50"
- Document: "2,500.00" → Output: "2,500.00" (already correct)"""
        elif decimal_sep == '.' and not thousand_sep:
            conversion_examples = """
Conversion examples:
- Document: "1,234.56" → Output: "1234.56"
- Document: "85.50" → Output: "85.50" (already correct)"""
        elif decimal_sep == ',' and not thousand_sep:
            conversion_examples = """
Esempi conversione:
- Documento: "1.234,56" → Output: "1234,56"
- Documento: "85,50" → Output: "85,50" (già corretto)"""

        # Build column-specific rules
        column_rules = []
        for col in sorted(selected_columns, key=lambda x: x['order']):
            col_lower = col['output_name'].lower()
            col_type = col.get('type', 'text')

            if col_type == 'currency' or any(word in col_lower for word in ['amount', 'importo', 'debit', 'credit', 'dare', 'avere', 'balance', 'saldo', 'entrate', 'uscite', 'addebiti', 'accrediti']):
                column_rules.append(f"- {col['output_name']}: importo numerico formattato come specificato sopra")
            elif col_type == 'date' or any(word in col_lower for word in ['date', 'data']):
                column_rules.append(f"- {col['output_name']}: data esattamente come nel documento")
            else:
                column_rules.append(f"- {col['output_name']}: testo esattamente come nel documento")

        column_rules_text = "\n".join(column_rules)

        # Detect bank type for specific hints
        bank_hint = ""
        if "unicredit" in document_text.lower():
            bank_hint = """
BANK SPECIFIC RULES (UNICREDIT):
- The text extraction might flatten the 'Uscite' and 'Entrate' columns into a single sequence.
- You MUST use the DESCRIPTION to determine if an amount is a Debit (Uscite) or Credit (Entrate).
- KEYWORDS FOR ENTRATE (CREDIT/ACCREDITI): "BONIFICO A VOSTRO FAVORE", "VERSAMENTO", "INCASSO", "ACCREDITO", "STIPENDIO".
- KEYWORDS FOR USCITE (DEBIT/ADDEBITI): "PAGAMENTO", "ADDEBITO", "DISPOSIZIONE", "PRELIEVO", "COMMISSIONI", "IMPOSTA".
- If a row has only one amount, place it in the correct column based on these keywords.
- If it's an Entrata, put "0,00" (or empty) in Uscite and the amount in Entrate.
- If it's an Uscita, put the amount in Uscite and "0,00" (or empty) in Entrate.
"""

        # Build main prompt based on language
        if language == Language.IT:
            prompt = f"""Estrai tutte le righe di movimenti da questo estratto conto.

TESTO DOCUMENTO:
{document_text}

COLONNE DA ESTRARRE (in questo ordine esatto): {column_order}

REGOLE ESTRAZIONE:
1. Estrai SOLO righe di movimenti effettivi (transazioni, operazioni)
2. NON estrarre righe che contengono SOLO questi termini: {', '.join(keywords['balance_terms'] + keywords['summary_terms'])}
3. Ogni riga deve avere ESATTAMENTE {len(column_names)} valori
4. Se una cella è vuota, usa stringa vuota ""
{bank_hint}
FORMATO NUMERI - Converti tutti gli importi in questo formato:
{number_format_spec}
{conversion_examples}

REGOLE PER COLONNA:
{column_rules_text}

IMPORTANTE PER LE DATE:
- OGNI riga deve avere TUTTE le sue date compilate
- NON lasciare celle di date vuote
- Se la stessa data si ripete, SCRIVILA comunque in ogni riga
- Ogni transazione deve essere completa e autosufficiente

OUTPUT:
- Array JSON di array (ogni riga = array di stringhe)
- NO intestazioni colonne
- Celle vuote = ""
- Sostituisci i newline nei campi di testo con uno spazio singolo
- CRITICO: Ogni riga deve avere TUTTI i {len(column_names)} valori compilati

ESEMPIO OUTPUT:
[
  ["05/02/2025", "05/02/2025", "PAGAMENTO POS", "17{decimal_sep}50", ""],
  ["05/02/2025", "04/30/2025", "BOLLETTA", "599{decimal_sep}27", ""],
  ["06/02/2025", "06/02/2025", "ALTRA TRANSAZIONE", "100{decimal_sep}00", ""]
]

Nota: Anche se più righe hanno la stessa data, INCLUDI sempre la data in ogni riga.

Ritorna SOLO l'array JSON, nessun testo aggiuntivo."""

        else:  # English
            prompt = f"""Extract all transaction rows from this bank statement.

DOCUMENT TEXT:
{document_text}

COLUMNS TO EXTRACT (in this exact order): {column_order}

EXTRACTION RULES:
1. Extract ONLY actual transaction rows (real movements, operations)
2. DO NOT extract rows containing ONLY these terms: {', '.join(keywords['balance_terms'] + keywords['summary_terms'])}
3. Each row must have EXACTLY {len(column_names)} values
4. If a cell is empty, use empty string ""

NUMBER FORMAT - Convert all amounts to this format:
{number_format_spec}
{conversion_examples}

COLUMN RULES:
{column_rules_text}

IMPORTANT FOR DATES:
- EVERY row must have ALL its dates filled
- DO NOT leave date cells empty
- If the same date repeats, WRITE it anyway in every row
- Each transaction must be complete and self-contained

OUTPUT:
- JSON array of arrays (each row = string array)
- NO column headers
- Empty cells = ""
- Replace newlines in text fields with single space
- CRITICAL: Every row must have ALL {len(column_names)} values filled

EXAMPLE OUTPUT:
[
  ["05/02/2025", "05/02/2025", "POS PAYMENT", "17{decimal_sep}50", ""],
  ["05/02/2025", "04/30/2025", "BILL PAYMENT", "599{decimal_sep}27", ""],
  ["06/02/2025", "06/02/2025", "ANOTHER TRANSACTION", "100{decimal_sep}00", ""]
]

Note: Even if multiple rows have the same date, ALWAYS include the date in every row.

Return ONLY the JSON array, no additional text."""

        return prompt

    @staticmethod
    def get_simplified_prompt(original_prompt: str, language: Language = Language.EN) -> str:
        """
        Create a simplified version of a prompt for retry attempts

        Args:
            original_prompt: Original complex prompt
            language: Language for simplification

        Returns:
            Simplified prompt
        """
        if language == Language.IT:
            return """Estrai i dati in formato JSON array.
Regole:
1. Solo righe di movimenti
2. NO totali, saldi, o somme
3. Formato: array di array di stringhe
4. Rispetta l'ordine delle colonne specificato

Ritorna SOLO il JSON array."""
        else:
            return """Extract data as JSON array.
Rules:
1. Only transaction rows
2. NO totals, balances, or sums
3. Format: array of string arrays
4. Respect specified column order

Return ONLY the JSON array."""
