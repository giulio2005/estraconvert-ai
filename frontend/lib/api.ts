// API client for backend communication

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface UploadResponse {
  document_id: string;
  file_name: string;
  file_type: string;
  size_mb: number;
}

export interface DetectColumnsResponse {
  document_id: string;
  columns: Array<{
    id: string;
    name: string;
    type: 'text' | 'number' | 'date' | 'currency';
    sample_data: string[];
    confidence: number;
  }>;
  processing_time: number;
}

export interface ExtractDataResponse {
  document_id: string;
  data: string[][];
  rows_extracted: number;
  processing_time: number;
}

// Job status types for async operations
export interface JobResponse {
  job_id: string;
  status: 'PENDING' | 'PROCESSING' | 'SUCCESS' | 'FAILURE';
  message: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: 'PENDING' | 'PROCESSING' | 'SUCCESS' | 'FAILURE';
  progress?: number;
  step?: string;
  result?: unknown;
  error?: string;
}

// Helper function for polling job status
async function pollJobResult<T>(
  jobId: string,
  onProgress?: (progress: number, step: string) => void
): Promise<T> {
  const pollInterval = 1000; // 1 second
  const maxAttempts = 300; // Max 5 minutes

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const response = await fetch(`${API_BASE_URL}/api/jobs/${jobId}`);

    if (!response.ok) {
      throw new Error('Failed to check job status');
    }

    const status: JobStatusResponse = await response.json();

    // Update progress callback
    if (onProgress && status.progress !== undefined && status.step) {
      onProgress(status.progress, status.step);
    }

    // Job completed successfully
    if (status.status === 'SUCCESS' && status.result) {
      return status.result as T;
    }

    // Job failed
    if (status.status === 'FAILURE') {
      throw new Error(status.error || 'Job failed');
    }

    // Still processing, wait and retry
    await new Promise(resolve => setTimeout(resolve, pollInterval));
  }

  throw new Error('Job timeout - exceeded maximum polling time');
}

export const api = {
  async uploadDocument(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
  },

  // SYNC: Original column detection (kept for backward compatibility)
  async detectColumns(documentId: string): Promise<DetectColumnsResponse> {
    const formData = new FormData();
    formData.append('document_id', documentId);

    const response = await fetch(`${API_BASE_URL}/api/detect-columns`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Column detection failed');
    }

    return response.json();
  },

  // ASYNC: Column detection with progress tracking
  async detectColumnsAsync(
    documentId: string,
    onProgress?: (progress: number, step: string) => void
  ): Promise<DetectColumnsResponse> {
    const formData = new FormData();
    formData.append('document_id', documentId);

    // Start async job
    const response = await fetch(`${API_BASE_URL}/api/detect-columns-async`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to start column detection');
    }

    const { job_id }: JobResponse = await response.json();

    // Poll for results
    return pollJobResult<DetectColumnsResponse>(job_id, onProgress);
  },

  // SYNC: Original data extraction (kept for backward compatibility)
  async extractData(
    documentId: string,
    selectedColumns: Array<{
      id: string;
      name: string;
      type: string;
      output_name: string;
      order: number;
    }>,
    formatConfig: {
      delimiter: string;
      decimal_separator: string;
      thousands_separator: string;
      date_format: string;
      encoding: string;
      include_headers: boolean;
    }
  ): Promise<ExtractDataResponse> {
    const response = await fetch(`${API_BASE_URL}/api/extract-data`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        document_id: documentId,
        selected_columns: selectedColumns,
        format_config: formatConfig,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Data extraction failed');
    }

    return response.json();
  },

  // ASYNC: Data extraction with progress tracking
  async extractDataAsync(
    documentId: string,
    selectedColumns: Array<{
      id: string;
      name: string;
      type: string;
      output_name: string;
      order: number;
    }>,
    formatConfig: {
      delimiter: string;
      decimal_separator: string;
      thousands_separator: string;
      date_format: string;
      encoding: string;
      include_headers: boolean;
    },
    onProgress?: (progress: number, step: string) => void
  ): Promise<ExtractDataResponse> {
    // Start async job
    const response = await fetch(`${API_BASE_URL}/api/extract-data-async`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        document_id: documentId,
        selected_columns: selectedColumns,
        format_config: formatConfig,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to start data extraction');
    }

    const { job_id }: JobResponse = await response.json();

    // Poll for results
    return pollJobResult<ExtractDataResponse>(job_id, onProgress);
  },

  // ==================== EXCEL-SPECIFIC ENDPOINTS ====================

  /**
   * Detect columns in Excel file (instant, no AI needed)
   */
  async detectColumnsExcel(documentId: string, sheetName?: string): Promise<DetectColumnsResponse> {
    const formData = new FormData();
    formData.append('document_id', documentId);
    if (sheetName) {
      formData.append('sheet_name', sheetName);
    }

    const response = await fetch(`${API_BASE_URL}/api/detect-columns-excel`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Excel column detection failed');
    }

    return response.json();
  },

  /**
   * Get all sheet names from Excel file
   */
  async getExcelSheets(documentId: string): Promise<{ sheets: string[]; sheet_count: number }> {
    const response = await fetch(`${API_BASE_URL}/api/excel-sheets/${documentId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get Excel sheets');
    }

    return response.json();
  },

  /**
   * Extract data from Excel file and convert to CSV (instant, no AI needed)
   */
  async extractDataExcel(
    documentId: string,
    selectedColumns: Array<{
      id: string;
      name: string;
      type: string;
      output_name: string;
      order: number;
    }>,
    formatConfig: {
      delimiter: string;
      decimal_separator: string;
      thousands_separator: string;
      date_format: string;
      encoding: string;
      include_headers: boolean;
    }
  ): Promise<ExtractDataResponse> {
    const response = await fetch(`${API_BASE_URL}/api/extract-data-excel`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        document_id: documentId,
        selected_columns: selectedColumns,
        format_config: formatConfig,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Excel extraction failed');
    }

    return response.json();
  },
};
