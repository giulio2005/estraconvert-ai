'use client';

import { useState } from 'react';
import Header from '@/components/layout/Header';
import { FileUpload } from '@/components/upload/FileUpload';
import { ColumnSelector } from '@/components/column-selector/ColumnSelector';
import { FormatConfig } from '@/components/format-config/FormatConfig';
import { PreviewAndDownload } from '@/components/preview/PreviewAndDownload';
import { Progress } from '@/components/ui/progress';
import type {
  ConversionState,
  UploadedDocument,
  DetectedColumn,
  SelectedColumn,
  FormatConfig as FormatConfigType,
} from '@/lib/types/index';
import { api } from '@/lib/api';

const DEFAULT_FORMAT_CONFIG: FormatConfigType = {
  delimiter: ';',
  decimalSeparator: ',',
  thousandsSeparator: '.',
  dateFormat: 'DD/MM/YYYY',
  encoding: 'UTF-8',
  includeHeaders: true,
};

export default function Home() {
  const [state, setState] = useState<ConversionState>({
    step: 'upload',
    document: null,
    detectedColumns: [],
    selectedColumns: [],
    formatConfig: DEFAULT_FORMAT_CONFIG,
    extractedData: [],
    isProcessing: false,
    error: null,
  });

  const handleFileUpload = async (document: UploadedDocument) => {
    setState((prev) => ({ ...prev, document, isProcessing: true, error: null }));

    try {
      // 1. Upload document to backend
      const uploadResponse = await api.uploadDocument(document.file);
      console.log('Document uploaded:', uploadResponse);

      // 2. Detect columns using AI
      const detectResponse = await api.detectColumns(uploadResponse.document_id);
      console.log('Columns detected:', detectResponse);

      // Map API response to frontend types
      const detectedColumns: DetectedColumn[] = detectResponse.columns.map((col) => ({
        id: col.id,
        name: col.name,
        type: col.type,
        sampleData: col.sample_data,
        confidence: col.confidence,
      }));

      setState((prev) => ({
        ...prev,
        detectedColumns,
        step: 'selection',
        isProcessing: false,
        document: {
          ...document,
          id: uploadResponse.document_id, // Store document ID for later use
        },
      }));
    } catch (error) {
      console.error('Error during upload/detection:', error);
      setState((prev) => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Si è verificato un errore',
        isProcessing: false,
      }));
    }
  };

  const handleColumnsSelected = (columns: SelectedColumn[]) => {
    setState((prev) => ({ ...prev, selectedColumns: columns }));
  };

  const handleNextToFormat = () => {
    setState((prev) => ({ ...prev, step: 'format' }));
  };

  const handleFormatConfigChange = (formatConfig: FormatConfigType) => {
    setState((prev) => ({ ...prev, formatConfig }));
  };

  const handleGenerateCSV = async () => {
    setState((prev) => ({ ...prev, isProcessing: true, error: null }));

    try {
      if (!state.document?.id) {
        throw new Error('Document ID not found');
      }

      // Extract data using AI
      const extractResponse = await api.extractData(
        state.document.id,
        state.selectedColumns.map((col) => ({
          id: col.id,
          name: col.name,
          type: col.type,
          output_name: col.outputName,
          order: col.order,
        })),
        {
          delimiter: state.formatConfig.delimiter,
          decimal_separator: state.formatConfig.decimalSeparator,
          thousands_separator: state.formatConfig.thousandsSeparator,
          date_format: state.formatConfig.dateFormat,
          encoding: state.formatConfig.encoding,
          include_headers: state.formatConfig.includeHeaders,
        }
      );

      console.log('Data extracted:', extractResponse);
      console.log('📊 Total rows received:', extractResponse.data?.length);
      console.log('🔍 First row:', extractResponse.data?.[0]);
      console.log('🔍 Second row:', extractResponse.data?.[1]);

      setState((prev) => ({
        ...prev,
        extractedData: extractResponse.data,
        step: 'preview',
        isProcessing: false,
      }));
    } catch (error) {
      console.error('Error during data extraction:', error);
      setState((prev) => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Errore durante estrazione dati',
        isProcessing: false,
      }));
    }
  };

  const handleDownload = () => {
    const { selectedColumns, extractedData, formatConfig } = state;

    // Build CSV content
    let csvContent = '';

    // Add headers if enabled
    if (formatConfig.includeHeaders) {
      const headers = selectedColumns.map((col) => col.outputName).join(formatConfig.delimiter);
      csvContent += headers + '\n';
    }

    // Add data rows
    extractedData.forEach((row) => {
      const formattedRow = row.join(formatConfig.delimiter);
      csvContent += formattedRow + '\n';
    });

    // Create blob and download
    const blob = new Blob([csvContent], {
      type: `text/csv;charset=${formatConfig.encoding}`,
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `estratto_${new Date().getTime()}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleReset = () => {
    if (state.document) {
      URL.revokeObjectURL(state.document.preview);
    }
    setState({
      step: 'upload',
      document: null,
      detectedColumns: [],
      selectedColumns: [],
      formatConfig: DEFAULT_FORMAT_CONFIG,
      extractedData: [],
      isProcessing: false,
      error: null,
    });
  };

  const getProgress = () => {
    switch (state.step) {
      case 'upload':
        return 0;
      case 'selection':
        return 33;
      case 'format':
        return 66;
      case 'preview':
        return 100;
      default:
        return 0;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />

      {/* Progress Bar */}
      {state.step !== 'upload' && (
        <div className="border-b bg-muted/30">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center gap-4">
              <Progress value={getProgress()} className="flex-1" />
              <span className="text-sm text-muted-foreground font-medium">
                {state.step === 'selection' && 'Selezione Colonne'}
                {state.step === 'format' && 'Configurazione Formato'}
                {state.step === 'preview' && 'Anteprima e Download'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="container mx-auto px-4 py-12">
        {/* Error Display */}
        {state.error && (
          <div className="max-w-2xl mx-auto mb-8 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start gap-3">
              <div className="text-red-600 mt-0.5">⚠️</div>
              <div>
                <p className="font-medium text-red-900">Errore</p>
                <p className="text-sm text-red-700 mt-1">{state.error}</p>
              </div>
            </div>
          </div>
        )}

        {state.isProcessing && (
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 rounded-full">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
              <span className="text-sm font-medium">
                {state.step === 'upload' && 'Rilevamento colonne in corso...'}
                {state.step === 'format' && 'Generazione CSV...'}
              </span>
            </div>
          </div>
        )}

        {state.step === 'upload' && (
          <FileUpload onFileUpload={handleFileUpload} isProcessing={state.isProcessing} />
        )}

        {state.step === 'selection' && (
          <ColumnSelector
            detectedColumns={state.detectedColumns}
            onColumnsSelected={handleColumnsSelected}
            onNext={handleNextToFormat}
          />
        )}

        {state.step === 'format' && (
          <FormatConfig
            config={state.formatConfig}
            onChange={handleFormatConfigChange}
            onNext={handleGenerateCSV}
          />
        )}

        {state.step === 'preview' && (
          <PreviewAndDownload
            data={state.extractedData}
            columns={state.selectedColumns}
            formatConfig={state.formatConfig}
            onDownload={handleDownload}
            onReset={handleReset}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t mt-24">
        <div className="container mx-auto px-4 py-8 text-center text-sm text-muted-foreground">
          <p>EstraConvert MVP - Convertitore intelligente di documenti contabili</p>
        </div>
      </footer>
    </div>
  );
}
