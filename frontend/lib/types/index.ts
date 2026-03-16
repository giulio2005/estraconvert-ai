// Core types for the application

export interface UploadedDocument {
  id: string;
  file: File;
  preview: string;
  type: 'pdf' | 'image';
}

export interface DetectedColumn {
  id: string;
  name: string;
  type: 'text' | 'number' | 'date' | 'currency';
  sampleData: string[];
  confidence: number;
}

export interface SelectedColumn extends DetectedColumn {
  order: number;
  outputName: string;
  selected?: boolean;
}

export interface FormatConfig {
  delimiter: ',' | ';' | '|' | '\t';
  decimalSeparator: '.' | ',';
  thousandsSeparator: '.' | ',' | ' ' | 'none';
  dateFormat: string;
  encoding: 'UTF-8' | 'ISO-8859-1';
  includeHeaders: boolean;
}

export interface ConversionState {
  step: 'upload' | 'detection' | 'selection' | 'format' | 'preview';
  document: UploadedDocument | null;
  detectedColumns: DetectedColumn[];
  selectedColumns: SelectedColumn[];
  formatConfig: FormatConfig;
  extractedData: string[][];
  isProcessing: boolean;
  error: string | null;
}

export const DEFAULT_FORMAT_CONFIG: FormatConfig = {
  delimiter: ';',
  decimalSeparator: ',',
  thousandsSeparator: '.',
  dateFormat: 'DD/MM/YYYY',
  encoding: 'UTF-8',
  includeHeaders: true,
};
