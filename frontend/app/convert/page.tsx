'use client';

import { useState } from 'react';
import Header from '@/components/layout/Header';
import Footer from '@/components/layout/Footer';
import { CloudUpload, CheckCircle, GripVertical, Download, FileText, DollarSign, Plus, Minus, Table2, Code, AlertCircle, Loader2, Settings, Calendar, ChevronDown } from 'lucide-react';
import { api } from '@/lib/api';

interface Column {
  id: string;
  name: string;
  selected: boolean;
  order: number;
  type?: string;
}

export default function ConvertPage() {
  const [fileName, setFileName] = useState<string>('');
  const [documentId, setDocumentId] = useState<string>('');
  const [fileType, setFileType] = useState<string>(''); // Track if file is excel, pdf, or image
  const [showSections, setShowSections] = useState(false);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [previewMode, setPreviewMode] = useState<'table' | 'csv'>('table');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detectProgress, setDetectProgress] = useState<number | null>(null);
  const [detectStep, setDetectStep] = useState<string>('');
  const [extractProgress, setExtractProgress] = useState<number | null>(null);
  const [extractStep, setExtractStep] = useState<string>('');
  const [extractedData, setExtractedData] = useState<string[][]>([]);
  const [hasExtracted, setHasExtracted] = useState(false);

  const [columns, setColumns] = useState<Column[]>([]);

  // Accordion state for expandable sections
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['delimiter']));

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const [config, setConfig] = useState({
    delimiter: ';',
    decimal: 'original' as string | 'original',
    thousand: 'original' as string | 'original',
    addPlus: false,
    addMinus: true,
    includeCurrency: false,
    currencySymbol: '€',
    currencyPosition: 'before' as 'before' | 'after',
    includeHeaders: false, // Disabled by default - no column headers in output
    dateSeparator: 'original' as string | 'original',
    dateFormat: 'original' as 'DD/MM/YYYY' | 'MM/DD/YYYY' | 'YYYY-MM-DD' | 'DD-MM-YYYY' | 'MM-DD-YYYY' | 'original',
  });

  const handleFileSelect = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.jpg,.jpeg,.png,.xlsx,.xls';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        setFileName(file.name);
        setIsProcessing(true);
        setError(null);

        try {
          // 1. Upload document
          const uploadResponse = await api.uploadDocument(file);
          setDocumentId(uploadResponse.document_id);
          setFileType(uploadResponse.file_type);

          const isExcel = uploadResponse.file_type === 'excel';

          // 2. Detect columns (Excel is instant, PDF uses async with progress)
          let detectResponse;

          if (isExcel) {
            // Excel: instant detection, no progress bar needed
            detectResponse = await api.detectColumnsExcel(uploadResponse.document_id);
          } else {
            // PDF/Image: async with progress tracking
            setDetectProgress(0);
            detectResponse = await api.detectColumnsAsync(
              uploadResponse.document_id,
              (progress, step) => {
                console.log(`📊 Detection Progress: ${progress}% - ${step}`);
                setDetectProgress(progress);
                setDetectStep(step);
              }
            );
          }

          // 3. Map detected columns to our format
          const detectedColumns: Column[] = detectResponse.columns.map((col, idx) => ({
            id: col.id,
            name: col.name,
            selected: true,
            order: idx,
            type: col.type,
          }));

          setColumns(detectedColumns);
          setShowSections(true);
          setHasExtracted(false);
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Si è verificato un errore');
          console.error('Error:', err);
        } finally {
          setIsProcessing(false);
          setDetectProgress(null);
          setDetectStep('');
        }
      }
    };
    input.click();
  };

  const handleConvert = async () => {
    if (!documentId || columns.filter(c => c.selected).length === 0) {
      setError('Seleziona almeno una colonna da estrarre');
      return;
    }

    setIsExtracting(true);
    setError(null);
    setExtractProgress(0);

    try {
      const selectedCols = columns
        .filter(c => c.selected)
        .sort((a, b) => a.order - b.order)
        .map(col => ({
          id: col.id,
          name: col.name,
          type: col.type || 'text',
          output_name: col.name,
          order: col.order,
        }));

      // Convert 'original' to concrete values for backend (backend doesn't understand 'original')
      const formatConfig = {
        delimiter: config.delimiter,
        decimal_separator: config.decimal === 'original' ? ',' : config.decimal,
        thousands_separator: config.thousand === 'original' ? '.' : config.thousand,
        date_format: 'DD/MM/YYYY',
        encoding: 'UTF-8',
        include_headers: true,
      };

      // Use appropriate endpoint based on file type
      let response;
      if (fileType === 'excel') {
        // Excel: instant extraction, no progress needed
        response = await api.extractDataExcel(documentId, selectedCols, formatConfig);
      } else {
        // PDF/Image: async with progress tracking
        response = await api.extractDataAsync(
          documentId,
          selectedCols,
          formatConfig,
          (progress, step) => {
            console.log(`📊 Extraction Progress: ${progress}% - ${step}`);
            setExtractProgress(progress);
            setExtractStep(step);
          }
        );
      }

      console.log('🔍 DEBUG: Extract response:', response);
      console.log('🔍 DEBUG: Total rows received:', response.data?.length);
      console.log('🔍 DEBUG: First row:', response.data?.[0]);
      console.log('🔍 DEBUG: Second row:', response.data?.[1]);

      setExtractedData(response.data);
      setHasExtracted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Estrazione dati fallita');
      console.error('Extraction error:', err);
    } finally {
      setIsExtracting(false);
      setExtractProgress(null);
      setExtractStep('');
    }
  };

  const handleEditOutput = () => {
    // Reset to column selection phase (keep columns detected, clear extraction results)
    setHasExtracted(false);
    setExtractedData([]);
    setExtractProgress(null);
    setExtractStep('');
    // User can now reselect columns and modify output settings, then click "Converti" again
  };

  const toggleColumn = (id: string) => {
    const updatedColumns = columns.map(col =>
      col.id === id ? { ...col, selected: !col.selected } : col
    );
    setColumns(updatedColumns);
    setHasExtracted(false); // Reset extracted state when columns change
  };

  const handleDragStart = (index: number) => {
    setDraggedIndex(index);
  };

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    if (draggedIndex === null || draggedIndex === index) return;

    const newColumns = [...columns];
    const draggedItem = newColumns[draggedIndex];
    newColumns.splice(draggedIndex, 1);
    newColumns.splice(index, 0, draggedItem);

    // Update order
    newColumns.forEach((col, idx) => col.order = idx);

    setColumns(newColumns);
    setDraggedIndex(index);
    setHasExtracted(false); // Reset extracted state when order changes
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
  };

  const getFormattedTableData = () => {
    // Use extracted data from backend
    // Backend returns pure data rows (no header row)
    if (extractedData.length === 0) return [];

    const dataRows = extractedData; // No need to skip - backend returns data only
    const selectedCols = columns.filter(c => c.selected).sort((a, b) => a.order - b.order);

    // Apply formatting to each cell based on column type
    return dataRows.map(row =>
      row.map((cell, idx) => {
        const column = selectedCols[idx];
        return formatValue(cell, column?.type, column?.name);
      })
    );
  };

  const formatDate = (value: string): string => {
    // If format is 'original', don't change anything
    if (config.dateFormat === 'original' && config.dateSeparator === 'original') {
      return value;
    }

    // Try to parse various date formats
    // Common formats: "DD/MM/YYYY", "DD-MM-YYYY", "DD.MM.YYYY", "YYYY-MM-DD", "MM/DD/YYYY"

    let day: string, month: string, year: string;

    // Remove any time component if present
    const dateOnly = value.split(' ')[0];

    // Try to detect and parse the date
    const parts = dateOnly.split(/[\/\-\.]/); // Split by /, -, or .

    if (parts.length !== 3) {
      // Can't parse, return original
      return value;
    }

    // Detect format based on part lengths and values
    if (parts[0].length === 4) {
      // YYYY-MM-DD format
      year = parts[0];
      month = parts[1];
      day = parts[2];
    } else if (parseInt(parts[0]) > 12) {
      // DD/MM/YYYY or DD-MM-YYYY (day > 12, so must be day first)
      day = parts[0];
      month = parts[1];
      year = parts[2];
    } else if (parseInt(parts[1]) > 12) {
      // MM/DD/YYYY (month first, day > 12)
      month = parts[0];
      day = parts[1];
      year = parts[2];
    } else {
      // Ambiguous - default to DD/MM/YYYY (European format)
      day = parts[0];
      month = parts[1];
      year = parts[2];
    }

    // Pad with zeros if needed
    day = day.padStart(2, '0');
    month = month.padStart(2, '0');

    // Detect original separator if needed
    const separator = config.dateSeparator === 'original'
      ? (dateOnly.includes('/') ? '/' : dateOnly.includes('-') ? '-' : '.')
      : config.dateSeparator;

    // Apply selected format
    let formatted: string;
    const format = config.dateFormat === 'original' ? 'DD/MM/YYYY' : config.dateFormat;

    switch (format) {
      case 'DD/MM/YYYY':
        formatted = `${day}${separator}${month}${separator}${year}`;
        break;
      case 'MM/DD/YYYY':
        formatted = `${month}${separator}${day}${separator}${year}`;
        break;
      case 'YYYY-MM-DD':
        formatted = `${year}${separator}${month}${separator}${day}`;
        break;
      case 'DD-MM-YYYY':
        formatted = `${day}${separator}${month}${separator}${year}`;
        break;
      default:
        formatted = `${day}${separator}${month}${separator}${year}`;
    }

    return formatted;
  };

  const formatValue = (value: string, columnType?: string, columnName?: string): string => {
    // Skip empty values
    if (!value || value === '') return value;

    // Handle date formatting first
    if (columnType === 'date') {
      return formatDate(value);
    }

    // Detect if it's a currency column
    const isCurrency = columnType === 'currency' ||
                       columnName?.toLowerCase().includes('importo') ||
                       columnName?.toLowerCase().includes('amount') ||
                       columnName?.toLowerCase().includes('debito') ||
                       columnName?.toLowerCase().includes('credito') ||
                       columnName?.toLowerCase().includes('debit') ||
                       columnName?.toLowerCase().includes('credit') ||
                       columnName?.toLowerCase().includes('dare') ||
                       columnName?.toLowerCase().includes('avere');

    if (!isCurrency) return value;

    // If both decimal and thousand are 'original', return value as-is (only add currency symbol if needed)
    if (config.decimal === 'original' && config.thousand === 'original') {
      if (config.includeCurrency) {
        const trimmed = value.replace(/[€$£¥₹₽₿]/g, '').trim();
        if (config.currencyPosition === 'before') {
          return config.currencySymbol + ' ' + trimmed;
        } else {
          return trimmed + ' ' + config.currencySymbol;
        }
      }
      return value;
    }

    // Remove existing currency symbols and trim
    const numValue = value.replace(/[€$£¥₹₽₿]/g, '').trim();

    // Detect if column is specifically for debits (negative) or credits (positive)
    const isDebitColumn = columnName?.toLowerCase().includes('debito') ||
                          columnName?.toLowerCase().includes('debit') ||
                          columnName?.toLowerCase().includes('dare') ||
                          columnName?.toLowerCase().includes('uscit');

    const isCreditColumn = columnName?.toLowerCase().includes('credito') ||
                           columnName?.toLowerCase().includes('credit') ||
                           columnName?.toLowerCase().includes('avere') ||
                           columnName?.toLowerCase().includes('entrat');

    // Check if value already has a sign
    const hasExistingSign = numValue.startsWith('-') || numValue.startsWith('+');

    // Remove existing signs for clean processing
    const cleanValue = numValue.replace(/^[+-]/, '');

    // Determine if value should be negative or positive
    let isNegative = false;
    let isPositive = false;

    if (hasExistingSign) {
      // Use existing sign
      isNegative = numValue.startsWith('-');
      isPositive = numValue.startsWith('+');
    } else {
      // Infer from column name
      if (isDebitColumn) {
        isNegative = true; // Debits are negative
      } else if (isCreditColumn) {
        isPositive = true; // Credits are positive
      } else {
        // Generic amount column - assume positive
        isPositive = true;
      }
    }

    // Parse the number - detect input format intelligently
    // Strategy:
    // - If there's only one separator, it's the decimal separator
    // - If there are multiple separators, the last one is decimal, others are thousands
    // - Common formats: "1,234.56" (EN), "1.234,56" (IT/DE), "1 234,56" (FR)

    let parsedNum: number;

    // Count occurrences of different separators
    const commaCount = (cleanValue.match(/,/g) || []).length;
    const dotCount = (cleanValue.match(/\./g) || []).length;
    const spaceCount = (cleanValue.match(/\s/g) || []).length;

    if (commaCount === 0 && dotCount === 0 && spaceCount === 0) {
      // No separators - plain integer
      parsedNum = parseFloat(cleanValue);
    } else if (commaCount === 0 && dotCount === 1) {
      // Only one dot - it's a decimal separator (e.g., "59.0", "1234.56")
      parsedNum = parseFloat(cleanValue);
    } else if (dotCount === 0 && commaCount === 1) {
      // Only one comma - it's a decimal separator (e.g., "59,0", "1234,56")
      parsedNum = parseFloat(cleanValue.replace(',', '.'));
    } else if (dotCount > 1 && commaCount === 0) {
      // Multiple dots - they're thousands separators, no decimals (e.g., "1.234.567")
      parsedNum = parseFloat(cleanValue.replace(/\./g, ''));
    } else if (commaCount > 1 && dotCount === 0) {
      // Multiple commas - they're thousands separators, no decimals (e.g., "1,234,567")
      parsedNum = parseFloat(cleanValue.replace(/,/g, ''));
    } else {
      // Mixed separators - determine which is decimal vs thousands
      const lastCommaPos = cleanValue.lastIndexOf(',');
      const lastDotPos = cleanValue.lastIndexOf('.');

      if (lastCommaPos > lastDotPos) {
        // Comma is decimal, dots/spaces are thousands (e.g., "1.234,56" or "1 234,56")
        parsedNum = parseFloat(cleanValue.replace(/[\.\s]/g, '').replace(',', '.'));
      } else {
        // Dot is decimal, commas/spaces are thousands (e.g., "1,234.56" or "1 234.56")
        parsedNum = parseFloat(cleanValue.replace(/[,\s]/g, ''));
      }
    }

    // If parsing failed, return original value
    if (isNaN(parsedNum)) {
      return value;
    }

    // Determine decimal places (default 2 for currency)
    const decimalPlaces = 2;

    // Split into integer and decimal parts
    const parts = parsedNum.toFixed(decimalPlaces).split('.');
    let integerPart = parts[0];
    const decimalPart = parts[1];

    // Apply thousands separator (if not 'original')
    if (config.thousand !== 'original' && config.thousand) {
      integerPart = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, config.thousand);
    }

    // Determine decimal separator
    const decimalSep = config.decimal === 'original' ? ',' : config.decimal;

    // Combine with decimal separator
    let formattedNumber = integerPart;
    if (decimalPart) {
      formattedNumber += decimalSep + decimalPart;
    }

    // Apply sign
    let result = formattedNumber;

    // DEBUG: Log sign application
    if (columnName?.toLowerCase().includes('debito') || columnName?.toLowerCase().includes('credito')) {
      console.log(`🔍 formatValue: ${columnName} | value="${value}" | isNegative=${isNegative} | isPositive=${isPositive} | addMinus=${config.addMinus} | addPlus=${config.addPlus}`);
    }

    if (isNegative && config.addMinus) {
      result = '-' + result;
    } else if (isPositive && config.addPlus) {
      result = '+' + result;
    } else if (isNegative && !config.addMinus) {
      result = formattedNumber;
    }

    // Add currency symbol if enabled
    if (config.includeCurrency) {
      if (config.currencyPosition === 'before') {
        result = config.currencySymbol + ' ' + result;
      } else {
        result = result + ' ' + config.currencySymbol;
      }
    }

    return result;
  };

  const generatePreview = () => {
    const delimiter = config.delimiter;
    const selectedCols = columns.filter(c => c.selected).sort((a, b) => a.order - b.order);

    if (extractedData.length === 0) {
      return 'Nessun dato disponibile';
    }

    let preview = '';

    // Backend returns pure data rows (no header row included)
    const dataRows = extractedData;

    // Add headers if enabled (generate from column names, not from data)
    if (config.includeHeaders) {
      preview = selectedCols.map(c => c.name).join(delimiter) + '\n';
    }

    // Process all data rows from backend
    dataRows.forEach(row => {
      const formattedRow = row.map((cell, idx) => {
        const column = selectedCols[idx];
        return formatValue(cell, column?.type, column?.name);
      });
      preview += formattedRow.join(delimiter) + '\n';
    });

    return preview;
  };

  const handleDownload = () => {
    const csvContent = generatePreview();
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'estratto_convertito.csv';
    link.click();
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />

      <main className="flex-1 max-w-6xl mx-auto px-6 py-8 w-full">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Convertitore Estratti Conto</h2>
          <p className="text-lg text-gray-600">Carica il tuo file e personalizza l&apos;output CSV</p>
        </div>

        {/* File Upload Section */}
        <section className="mb-12">
          <div className="bg-white rounded-2xl shadow-sm p-8">
            <div
              onClick={isProcessing ? undefined : handleFileSelect}
              className={`border-2 border-dashed rounded-xl p-12 text-center transition-all ${
                isProcessing
                  ? 'border-gray-300 bg-gray-50 cursor-not-allowed'
                  : 'border-blue-300 bg-blue-50 hover:bg-blue-100 hover:border-blue-500 cursor-pointer'
              }`}
            >
              <div className="space-y-6">
                <div className="w-20 h-20 bg-blue-600 rounded-full flex items-center justify-center mx-auto">
                  {isProcessing ? (
                    <Loader2 className="text-white animate-spin" size={32} />
                  ) : (
                    <CloudUpload className="text-white" size={32} />
                  )}
                </div>
                <div>
                  <h4 className="text-xl font-semibold text-gray-900 mb-2">
                    {isProcessing ? 'Elaborazione in corso...' : 'Carica il tuo estratto conto'}
                  </h4>
                  <p className="text-gray-600">
                    {isProcessing
                      ? 'Stiamo analizzando il documento con AI...'
                      : 'Supportiamo PDF e immagini (JPG, PNG)'}
                  </p>

                  {/* Progress Bar - Column Detection */}
                  {isProcessing && (
                    <div className="mt-6 space-y-2">
                      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                        <div
                          className="bg-blue-600 h-3 transition-all duration-500 rounded-full"
                          style={{ width: `${detectProgress || 0}%` }}
                        />
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-700 font-medium">{detectStep || 'Avvio rilevamento...'}</span>
                        <span className="text-blue-600 font-bold">{detectProgress || 0}%</span>
                      </div>
                    </div>
                  )}
                </div>
                <button
                  disabled={isProcessing}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isProcessing ? 'Elaborazione...' : 'Seleziona file'}
                </button>
              </div>
            </div>

            {/* Success Message */}
            {fileName && !isProcessing && !error && (
              <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center space-x-3">
                  <CheckCircle className="text-green-600" />
                  <div>
                    <p className="font-medium text-green-800">File caricato e analizzato con successo</p>
                    <p className="text-sm text-green-600">{fileName}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <AlertCircle className="text-red-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-red-800">Errore durante l&apos;elaborazione</p>
                    <p className="text-sm text-red-600 mt-1">{error}</p>
                    <button
                      onClick={() => {
                        setError(null);
                        setFileName('');
                        setShowSections(false);
                      }}
                      className="text-sm text-red-700 underline mt-2 hover:text-red-800"
                    >
                      Riprova
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Column Selection Section */}
        {showSections && (
          <section className="mb-12">
            <div className="bg-white rounded-2xl shadow-sm p-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-6">Seleziona e Ordina le Colonne</h3>
              <p className="text-gray-600 mb-8">Spunta le colonne da includere e trascinale per riordinarle</p>

              <div className="space-y-3">
                {columns.map((column, index) => (
                  <div
                    key={column.id}
                    draggable
                    onDragStart={() => handleDragStart(index)}
                    onDragOver={(e) => handleDragOver(e, index)}
                    onDragEnd={handleDragEnd}
                    className={`bg-gray-50 p-4 rounded-lg border-2 transition-all cursor-move hover:border-blue-300 ${
                      column.selected ? 'border-blue-200 bg-blue-50' : 'border-gray-200'
                    } ${draggedIndex === index ? 'opacity-50' : ''}`}
                  >
                    <div className="flex items-center space-x-4">
                      <GripVertical className="text-gray-400" size={20} />
                      <input
                        type="checkbox"
                        checked={column.selected}
                        onChange={() => toggleColumn(column.id)}
                        className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
                      />
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{column.name}</p>
                        <p className="text-sm text-gray-500 capitalize">{column.type || 'text'}</p>
                      </div>
                      <span className="text-sm text-gray-400">#{column.order + 1}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* Output Customization */}
        {showSections && (
          <section className="mb-12">
            <div className="bg-white rounded-2xl shadow-sm p-8">
              <div className="mb-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Personalizzazione Output CSV</h3>
                <p className="text-gray-600">Configura il formato di esportazione del file CSV</p>
              </div>

              <div className="space-y-4">
                {/* Delimiter */}
                <div className="border border-gray-200 rounded-xl overflow-hidden">
                  <button
                    onClick={() => toggleSection('delimiter')}
                    className="w-full bg-gradient-to-r from-blue-50 to-indigo-50 p-6 flex items-center justify-between hover:from-blue-100 hover:to-indigo-100 transition-all"
                  >
                    <div className="flex items-center">
                      <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center mr-3">
                        <FileText className="text-white" size={20} />
                      </div>
                      <div className="text-left">
                        <h4 className="text-base font-semibold text-gray-900">Delimitatore CSV</h4>
                        <p className="text-sm text-gray-600">Carattere tra le colonne</p>
                      </div>
                    </div>
                    <ChevronDown
                      className={`text-gray-600 transition-transform ${expandedSections.has('delimiter') ? 'rotate-180' : ''}`}
                      size={24}
                    />
                  </button>
                  {expandedSections.has('delimiter') && (
                    <div className="p-6 bg-white border-t border-gray-200">
                    <div className="grid grid-cols-2 gap-3">
                      {[
                        { value: ';', label: 'Punto e virgola', display: ';' },
                        { value: ',', label: 'Virgola', display: ',' },
                        { value: '|', label: 'Pipe', display: '|' },
                        { value: '\t', label: 'Tab', display: '→' },
                      ].map(option => (
                        <label key={option.value} className={`flex items-center justify-center p-4 rounded-lg cursor-pointer transition-all ${
                          config.delimiter === option.value
                            ? 'bg-blue-600 text-white shadow-lg scale-105'
                            : 'bg-white text-gray-700 hover:bg-blue-100 border-2 border-gray-200'
                        }`}>
                          <input
                            type="radio"
                            name="delimiter"
                            value={option.value}
                            checked={config.delimiter === option.value}
                            onChange={(e) => setConfig({ ...config, delimiter: e.target.value })}
                            className="sr-only"
                          />
                          <span className="font-mono text-2xl font-bold mr-2">{option.display}</span>
                          <span className="text-sm font-medium">{option.label}</span>
                        </label>
                      ))}
                    </div>
                    </div>
                  )}
                </div>

                {/* Decimal Separator */}
                <div className="border border-gray-200 rounded-xl overflow-hidden">
                  <button
                    onClick={() => toggleSection('decimal')}
                    className="w-full bg-gradient-to-r from-purple-50 to-pink-50 p-6 flex items-center justify-between hover:from-purple-100 hover:to-pink-100 transition-all"
                  >
                    <div className="flex items-center">
                      <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center mr-3">
                        <span className="text-white text-xl font-bold">.</span>
                      </div>
                      <div className="text-left">
                        <h4 className="text-base font-semibold text-gray-900">Separatore Decimale</h4>
                        <p className="text-sm text-gray-600">Per numeri con decimali</p>
                      </div>
                    </div>
                    <ChevronDown
                      className={`text-gray-600 transition-transform ${expandedSections.has('decimal') ? 'rotate-180' : ''}`}
                      size={24}
                    />
                  </button>
                  {expandedSections.has('decimal') && (
                    <div className="p-6 bg-white border-t border-gray-200">
                    <div className="grid grid-cols-3 gap-3">
                      {[
                        { value: 'original', label: 'Originale', example: 'Come da file' },
                        { value: ',', label: 'Virgola', example: '1.234,56' },
                        { value: '.', label: 'Punto', example: '1,234.56' },
                      ].map(option => (
                        <label key={option.value} className={`flex flex-col items-center p-3 rounded-lg cursor-pointer transition-all ${
                          config.decimal === option.value
                            ? 'bg-purple-600 text-white shadow-md'
                            : 'bg-white text-gray-700 hover:bg-purple-100 border-2 border-gray-200'
                        }`}>
                          <input
                            type="radio"
                            name="decimal"
                            value={option.value}
                            checked={config.decimal === option.value}
                            onChange={(e) => setConfig({ ...config, decimal: e.target.value })}
                            className="sr-only"
                          />
                          {option.value === 'original' ? (
                            <span className="text-sm font-semibold mb-1">{option.label}</span>
                          ) : (
                            <span className="font-mono text-2xl font-bold mb-1">{option.value}</span>
                          )}
                          {option.value !== 'original' && <span className="text-sm font-medium mb-1">{option.label}</span>}
                          <span className={`text-xs ${config.decimal === option.value ? 'text-purple-100' : 'text-gray-500'}`}>{option.example}</span>
                        </label>
                      ))}
                    </div>
                    </div>
                  )}
                </div>

                {/* Thousands Separator */}
                <div className="border border-gray-200 rounded-xl overflow-hidden">
                  <button
                    onClick={() => toggleSection('thousand')}
                    className="w-full bg-gradient-to-r from-green-50 to-emerald-50 p-6 flex items-center justify-between hover:from-green-100 hover:to-emerald-100 transition-all"
                  >
                    <div className="flex items-center">
                      <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center mr-3">
                        <span className="text-white text-xl font-bold">,</span>
                      </div>
                      <div className="text-left">
                        <h4 className="text-base font-semibold text-gray-900">Separatore Migliaia</h4>
                        <p className="text-sm text-gray-600">Per formattare grandi numeri</p>
                      </div>
                    </div>
                    <ChevronDown
                      className={`text-gray-600 transition-transform ${expandedSections.has('thousand') ? 'rotate-180' : ''}`}
                      size={24}
                    />
                  </button>
                  {expandedSections.has('thousand') && (
                    <div className="p-6 bg-white border-t border-gray-200">
                    <div className="grid grid-cols-3 gap-3">
                      {[
                        { value: 'original', label: 'Originale', display: '' },
                        { value: '.', label: 'Punto', display: '.' },
                        { value: ',', label: 'Virgola', display: ',' },
                        { value: ' ', label: 'Spazio', display: '_' },
                        { value: '', label: 'Nessuno', display: '' },
                      ].map(option => (
                        <label key={option.label} className={`flex flex-col items-center p-3 rounded-lg cursor-pointer transition-all ${
                          config.thousand === option.value
                            ? 'bg-green-600 text-white shadow-md'
                            : 'bg-white text-gray-700 hover:bg-green-100 border-2 border-gray-200'
                        }`}>
                          <input
                            type="radio"
                            name="thousand"
                            value={option.value}
                            checked={config.thousand === option.value}
                            onChange={(e) => setConfig({ ...config, thousand: e.target.value })}
                            className="sr-only"
                          />
                          {option.display && <span className="font-mono text-xl font-bold mb-1">{option.display}</span>}
                          <span className="text-sm font-medium">{option.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                  )}
                </div>

                {/* Signs (Plus/Minus) */}
                <div className="border border-gray-200 rounded-xl overflow-hidden">
                  <button
                    onClick={() => toggleSection('signs')}
                    className="w-full bg-gradient-to-r from-orange-50 to-amber-50 p-6 flex items-center justify-between hover:from-orange-100 hover:to-amber-100 transition-all"
                  >
                    <div className="flex items-center">
                      <div className="w-10 h-10 bg-orange-600 rounded-lg flex items-center justify-center mr-3">
                        <Plus className="text-white" size={20} />
                      </div>
                      <div className="text-left">
                        <h4 className="text-base font-semibold text-gray-900">Segno per Dare/Avere</h4>
                        <p className="text-sm text-gray-600">Gestione segni + e -</p>
                      </div>
                    </div>
                    <ChevronDown
                      className={`text-gray-600 transition-transform ${expandedSections.has('signs') ? 'rotate-180' : ''}`}
                      size={24}
                    />
                  </button>
                  {expandedSections.has('signs') && (
                    <div className="p-6 bg-white border-t border-gray-200">
                    <div className="space-y-3">
                      <label className={`flex items-start p-4 rounded-lg cursor-pointer transition-all ${
                        config.addPlus
                          ? 'bg-orange-600 text-white shadow-md'
                          : 'bg-white hover:bg-orange-100 border-2 border-gray-200'
                      }`}>
                        <input
                          type="checkbox"
                          checked={config.addPlus}
                          onChange={(e) => setConfig({ ...config, addPlus: e.target.checked })}
                          className="mt-1 mr-3 w-5 h-5 text-orange-600 rounded"
                        />
                        <div className="flex-1">
                          <div className="flex items-center">
                            <Plus size={18} className="mr-2" />
                            <p className="font-semibold">Aggiungi segno + per entrate</p>
                          </div>
                          <p className={`text-sm mt-1 ${config.addPlus ? 'text-orange-100' : 'text-gray-500'}`}>
                            Es: +1.250,00 invece di 1.250,00
                          </p>
                        </div>
                      </label>
                      <label className={`flex items-start p-4 rounded-lg cursor-pointer transition-all ${
                        config.addMinus
                          ? 'bg-orange-600 text-white shadow-md'
                          : 'bg-white hover:bg-orange-100 border-2 border-gray-200'
                      }`}>
                        <input
                          type="checkbox"
                          checked={config.addMinus}
                          onChange={(e) => setConfig({ ...config, addMinus: e.target.checked })}
                          className="mt-1 mr-3 w-5 h-5 text-orange-600 rounded"
                        />
                        <div className="flex-1">
                          <div className="flex items-center">
                            <Minus size={18} className="mr-2" />
                            <p className="font-semibold">Mantieni segno - per uscite</p>
                          </div>
                          <p className={`text-sm mt-1 ${config.addMinus ? 'text-orange-100' : 'text-gray-500'}`}>
                            Es: -85,50
                          </p>
                        </div>
                      </label>
                    </div>
                    </div>
                  )}
                </div>

                {/* Headers Toggle */}
                <div className="border border-gray-200 rounded-xl overflow-hidden">
                  <button
                    onClick={() => toggleSection('headers')}
                    className="w-full bg-gradient-to-r from-teal-50 to-cyan-50 p-6 flex items-center justify-between hover:from-teal-100 hover:to-cyan-100 transition-all"
                  >
                    <div className="flex items-center">
                      <div className="w-10 h-10 bg-teal-600 rounded-lg flex items-center justify-center mr-3">
                        <Table2 className="text-white" size={20} />
                      </div>
                      <div className="text-left">
                        <h4 className="text-base font-semibold text-gray-900">Intestazioni Colonne</h4>
                        <p className="text-sm text-gray-600">Prima riga del CSV</p>
                      </div>
                    </div>
                    <ChevronDown
                      className={`text-gray-600 transition-transform ${expandedSections.has('headers') ? 'rotate-180' : ''}`}
                      size={24}
                    />
                  </button>
                  {expandedSections.has('headers') && (
                    <div className="p-6 bg-white border-t border-gray-200">
                    <label className={`flex items-start p-4 rounded-lg cursor-pointer transition-all ${
                      config.includeHeaders
                        ? 'bg-teal-600 text-white shadow-md'
                        : 'bg-white hover:bg-teal-100 border-2 border-gray-200'
                    }`}>
                      <input
                        type="checkbox"
                        checked={config.includeHeaders}
                        onChange={(e) => setConfig({ ...config, includeHeaders: e.target.checked })}
                        className="mt-1 mr-3 w-5 h-5 text-teal-600 rounded"
                      />
                      <div className="flex-1">
                        <div className="flex items-center">
                          <CheckCircle size={18} className="mr-2" />
                          <p className="font-semibold">Includi intestazioni colonne</p>
                        </div>
                        <p className={`text-sm mt-1 ${config.includeHeaders ? 'text-teal-100' : 'text-gray-500'}`}>
                          Prima riga con nomi delle colonne
                        </p>
                      </div>
                    </label>
                    </div>
                  )}
                </div>

                {/* Currency Symbol */}
                <div className="border border-gray-200 rounded-xl overflow-hidden">
                  <button
                    onClick={() => toggleSection('currency')}
                    className="w-full bg-gradient-to-r from-emerald-50 to-teal-50 p-6 flex items-center justify-between hover:from-emerald-100 hover:to-teal-100 transition-all"
                  >
                    <div className="flex items-center">
                      <div className="w-10 h-10 bg-emerald-600 rounded-lg flex items-center justify-center mr-3">
                        <DollarSign className="text-white" size={20} />
                      </div>
                      <div className="text-left">
                        <h4 className="text-base font-semibold text-gray-900">Simbolo Valuta</h4>
                        <p className="text-sm text-gray-600">Aggiungi simbolo agli importi</p>
                      </div>
                    </div>
                    <ChevronDown
                      className={`text-gray-600 transition-transform ${expandedSections.has('currency') ? 'rotate-180' : ''}`}
                      size={24}
                    />
                  </button>
                  {expandedSections.has('currency') && (
                    <div className="p-6 bg-white border-t border-gray-200">
                    <label className={`flex items-start p-4 rounded-lg cursor-pointer transition-all mb-4 ${
                      config.includeCurrency
                        ? 'bg-emerald-600 text-white shadow-md'
                        : 'bg-white hover:bg-emerald-100 border-2 border-gray-200'
                    }`}>
                      <input
                        type="checkbox"
                        checked={config.includeCurrency}
                        onChange={(e) => setConfig({ ...config, includeCurrency: e.target.checked })}
                        className="mt-1 mr-3 w-5 h-5 text-emerald-600 rounded"
                      />
                      <div>
                        <p className="font-semibold">Includi simbolo valuta</p>
                        <p className={`text-sm mt-1 ${config.includeCurrency ? 'text-emerald-100' : 'text-gray-500'}`}>
                          Aggiungi € agli importi
                        </p>
                      </div>
                    </label>

                    {config.includeCurrency && (
                      <div className="space-y-4 bg-gray-50 rounded-lg p-4">
                        <div>
                          <label className="block text-sm font-semibold text-gray-900 mb-2">Simbolo</label>
                          <select
                            value={config.currencySymbol}
                            onChange={(e) => setConfig({ ...config, currencySymbol: e.target.value })}
                            className="w-full px-4 py-2 text-lg font-mono border-2 border-emerald-200 rounded-lg focus:border-emerald-500 focus:outline-none bg-white"
                          >
                            <option value="€">€ Euro</option>
                            <option value="$">$ Dollaro USA</option>
                            <option value="£">£ Sterlina</option>
                            <option value="¥">¥ Yen/Yuan</option>
                            <option value="₹">₹ Rupia</option>
                            <option value="₽">₽ Rublo</option>
                            <option value="₿">₿ Bitcoin</option>
                            <option value="Fr">Fr Franco Svizzero</option>
                            <option value="R$">R$ Real Brasiliano</option>
                            <option value="kr">kr Corona</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-semibold text-gray-900 mb-2">Posizione</label>
                          <div className="grid grid-cols-2 gap-3">
                            {[
                              { value: 'before', label: 'Prima', example: '€100' },
                              { value: 'after', label: 'Dopo', example: '100€' },
                            ].map(option => (
                              <label key={option.value} className={`flex flex-col items-center p-3 rounded-lg cursor-pointer transition-all ${
                                config.currencyPosition === option.value
                                  ? 'bg-emerald-600 text-white shadow-md'
                                  : 'bg-white hover:bg-emerald-100 border-2 border-gray-200'
                              }`}>
                                <input
                                  type="radio"
                                  name="currencyPosition"
                                  value={option.value}
                                  checked={config.currencyPosition === option.value}
                                  onChange={(e) => setConfig({ ...config, currencyPosition: e.target.value as 'before' | 'after' })}
                                  className="sr-only"
                                />
                                <span className="text-sm font-semibold mb-1">{option.label}</span>
                                <span className="text-xs font-mono opacity-75">{option.example}</span>
                              </label>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                    </div>
                  )}
                </div>

                {/* Date Format */}
                <div className="border border-gray-200 rounded-xl overflow-hidden">
                  <button
                    onClick={() => toggleSection('date')}
                    className="w-full bg-gradient-to-r from-purple-50 to-fuchsia-50 p-6 flex items-center justify-between hover:from-purple-100 hover:to-fuchsia-100 transition-all"
                  >
                    <div className="flex items-center">
                      <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center mr-3">
                        <Calendar className="text-white" size={20} />
                      </div>
                      <div className="text-left">
                        <h4 className="text-base font-semibold text-gray-900">Formato Data</h4>
                        <p className="text-sm text-gray-600">Personalizza separatore e ordine</p>
                      </div>
                    </div>
                    <ChevronDown
                      className={`text-gray-600 transition-transform ${expandedSections.has('date') ? 'rotate-180' : ''}`}
                      size={24}
                    />
                  </button>
                  {expandedSections.has('date') && (
                    <div className="p-6 bg-white border-t border-gray-200">
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-semibold text-gray-900 mb-2">Separatore</label>
                        <div className="grid grid-cols-4 gap-3">
                          {[
                            { value: 'original', label: 'Originale', example: '' },
                            { value: '/', label: 'Slash', example: '/' },
                            { value: '-', label: 'Trattino', example: '-' },
                            { value: '.', label: 'Punto', example: '.' },
                          ].map(option => (
                            <label key={option.value} className={`flex flex-col items-center p-3 rounded-lg cursor-pointer transition-all ${
                              config.dateSeparator === option.value
                                ? 'bg-purple-600 text-white shadow-md'
                                : 'bg-white hover:bg-purple-100 border-2 border-gray-200'
                            }`}>
                              <input
                                type="radio"
                                name="dateSeparator"
                                value={option.value}
                                checked={config.dateSeparator === option.value}
                                onChange={(e) => setConfig({ ...config, dateSeparator: e.target.value })}
                                className="sr-only"
                              />
                              <span className="text-sm font-semibold mb-1">{option.label}</span>
                              {option.example && <span className="text-xl font-mono opacity-75">{option.example}</span>}
                            </label>
                          ))}
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-semibold text-gray-900 mb-2">Formato</label>
                        <div className="grid grid-cols-2 gap-3">
                          {[
                            { value: 'original', label: 'Originale', example: 'Come da file' },
                            { value: 'DD/MM/YYYY', label: 'Giorno/Mese/Anno', example: '15/10/2025' },
                            { value: 'MM/DD/YYYY', label: 'Mese/Giorno/Anno', example: '10/15/2025' },
                            { value: 'YYYY-MM-DD', label: 'Anno-Mese-Giorno', example: '2025-10-15' },
                            { value: 'DD-MM-YYYY', label: 'Giorno-Mese-Anno', example: '15-10-2025' },
                          ].map(option => (
                            <label key={option.value} className={`flex flex-col p-3 rounded-lg cursor-pointer transition-all ${
                              config.dateFormat === option.value
                                ? 'bg-purple-600 text-white shadow-md'
                                : 'bg-white hover:bg-purple-100 border-2 border-gray-200'
                            }`}>
                              <input
                                type="radio"
                                name="dateFormat"
                                value={option.value}
                                checked={config.dateFormat === option.value}
                                onChange={(e) => setConfig({ ...config, dateFormat: e.target.value as 'DD/MM/YYYY' | 'MM/DD/YYYY' | 'YYYY-MM-DD' | 'DD-MM-YYYY' | 'MM-DD-YYYY' | 'original' })}
                                className="sr-only"
                              />
                              <span className="text-sm font-semibold mb-1">{option.label}</span>
                              <span className={`text-xs font-mono ${config.dateFormat === option.value ? 'text-purple-100' : 'text-gray-500'}`}>
                                {option.example.replace(/\//g, config.dateSeparator).replace(/-/g, config.dateSeparator)}
                              </span>
                            </label>
                          ))}
                        </div>
                      </div>
                    </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Convert Button */}
        {showSections && !hasExtracted && (
          <section className="mb-12">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl shadow-lg p-8 text-center">
              <h3 className="text-2xl font-bold text-white mb-4">Pronto per la conversione?</h3>
              <p className="text-blue-100 mb-6">
                {columns.filter(c => c.selected).length} colonne selezionate • Formato configurato
              </p>
              <button
                onClick={handleConvert}
                disabled={isExtracting || columns.filter(c => c.selected).length === 0}
                className="bg-white text-blue-600 px-12 py-4 rounded-xl font-bold text-lg hover:bg-blue-50 transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 inline-flex items-center space-x-3"
              >
                {isExtracting ? (
                  <>
                    <Loader2 className="animate-spin" size={24} />
                    <span>Estrazione in corso...</span>
                  </>
                ) : (
                  <>
                    <FileText size={24} />
                    <span>Converti Documento</span>
                  </>
                )}
              </button>

              {/* Progress Bar - Data Extraction */}
              {isExtracting && (
                <div className="mt-6 max-w-md mx-auto space-y-2">
                  <div className="w-full bg-blue-200 rounded-full h-3 overflow-hidden">
                    <div
                      className="bg-white h-3 transition-all duration-500 rounded-full shadow-sm"
                      style={{ width: `${extractProgress || 0}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-sm text-blue-100">
                    <span className="font-medium">{extractStep || 'Avvio estrazione...'}</span>
                    <span className="font-bold">{extractProgress || 0}%</span>
                  </div>
                </div>
              )}

              {columns.filter(c => c.selected).length === 0 && (
                <p className="text-blue-200 text-sm mt-4">Seleziona almeno una colonna per continuare</p>
              )}
            </div>
          </section>
        )}

        {/* Preview Section */}
        {hasExtracted && (
          <section className="mb-12">
            <div className="bg-white rounded-2xl shadow-sm p-8">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-2xl font-bold text-gray-900">Anteprima Output</h3>
                  <p className="text-gray-600 text-sm mt-1">
                    {extractedData.length > 0 ? `${extractedData.length - 1} righe estratte` : 'In attesa di dati...'}
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  {/* Edit Output Button (Excel only) */}
                  {fileType === 'excel' && (
                    <button
                      onClick={handleEditOutput}
                      className="flex items-center px-4 py-2 border-2 border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 transition-all"
                    >
                      <Settings size={18} className="mr-2" />
                      <span className="font-medium">Modifica Output</span>
                    </button>
                  )}

                  {/* View Toggle */}
                  <div className="flex bg-gray-100 rounded-lg p-1">
                    <button
                      onClick={() => setPreviewMode('table')}
                      className={`flex items-center px-4 py-2 rounded-md transition-all ${
                        previewMode === 'table'
                          ? 'bg-white text-blue-600 shadow-sm'
                          : 'text-gray-600 hover:text-gray-900'
                      }`}
                    >
                      <Table2 size={18} className="mr-2" />
                      <span className="font-medium">Tabella</span>
                    </button>
                    <button
                      onClick={() => setPreviewMode('csv')}
                      className={`flex items-center px-4 py-2 rounded-md transition-all ${
                        previewMode === 'csv'
                          ? 'bg-white text-blue-600 shadow-sm'
                          : 'text-gray-600 hover:text-gray-900'
                      }`}
                    >
                      <Code size={18} className="mr-2" />
                      <span className="font-medium">CSV Raw</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Fixed Height Preview Container */}
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                {/* Table View */}
                {previewMode === 'table' && (
                  <div className="h-96 overflow-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200">
                          {columns
                            .filter(c => c.selected)
                            .sort((a, b) => a.order - b.order)
                            .map((col, idx) => (
                              <th
                                key={col.id}
                                className="px-6 py-4 text-left text-sm font-semibold text-gray-900 whitespace-nowrap"
                              >
                                <div className="flex items-center space-x-2">
                                  <span className="text-xs text-blue-600 font-bold">#{idx + 1}</span>
                                  <span>{col.name}</span>
                                </div>
                              </th>
                            ))}
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {getFormattedTableData().map((row, rowIdx) => (
                          <tr
                            key={rowIdx}
                            className="hover:bg-gray-50 transition-colors"
                          >
                            {row.map((cell, cellIdx) => (
                              <td
                                key={cellIdx}
                                className="px-6 py-4 text-sm text-gray-700 whitespace-nowrap"
                              >
                                {cell}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* CSV Raw View */}
                {previewMode === 'csv' && (
                  <div className="h-96 overflow-auto bg-gray-900 p-6">
                    <pre className="text-green-400 font-mono text-sm whitespace-pre">{generatePreview()}</pre>
                  </div>
                )}

                {/* Legend/Info Bar */}
                <div className="bg-gray-50 px-6 py-3 border-t border-gray-200">
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    {previewMode === 'table' ? (
                      <>
                        <span>Mostrando {extractedData.length - 1} righe di dati</span>
                        <span>{columns.filter(c => c.selected).length} colonne selezionate</span>
                      </>
                    ) : (
                      <>
                        <div className="flex items-center space-x-4">
                          <span>Delimitatore: <span className="text-green-600 font-mono">{config.delimiter === '\t' ? '→ (tab)' : config.delimiter}</span></span>
                          <span>Decimale: <span className="text-green-600 font-mono">{config.decimal}</span></span>
                          <span>Migliaia: <span className="text-green-600 font-mono">{config.thousand || 'Nessuno'}</span></span>
                        </div>
                        <span>{generatePreview().split('\n').filter(line => line.trim()).length} righe totali</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Download Section */}
        {hasExtracted && (
          <section>
            <div className="bg-white rounded-2xl shadow-sm p-8 text-center">
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <Download className="text-green-600" size={32} />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">File CSV Pronto!</h3>
              <p className="text-gray-600 mb-8">Il tuo estratto conto è stato convertito con successo</p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <button
                  onClick={handleDownload}
                  className="bg-blue-600 text-white px-8 py-4 rounded-xl font-semibold text-lg hover:bg-blue-700 transition-colors inline-flex items-center justify-center"
                >
                  <Download className="mr-2" size={20} />
                  Scarica CSV
                </button>
                <button
                  onClick={() => window.location.reload()}
                  className="border-2 border-gray-300 text-gray-700 px-8 py-4 rounded-xl font-semibold text-lg hover:border-gray-400 transition-colors"
                >
                  Converti un altro file
                </button>
              </div>
            </div>
          </section>
        )}
      </main>

      <Footer />
    </div>
  );
}
