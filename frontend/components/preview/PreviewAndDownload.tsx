'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download, FileText, CheckCircle2 } from 'lucide-react';
import type { SelectedColumn, FormatConfig } from '@/lib/types';

interface PreviewAndDownloadProps {
  data: string[][];
  columns: SelectedColumn[];
  formatConfig: FormatConfig;
  onDownload: () => void;
  onReset: () => void;
}

export function PreviewAndDownload({
  data,
  columns,
  formatConfig,
  onDownload,
  onReset,
}: PreviewAndDownloadProps) {
  const totalRows = data.length;
  const hasHeaders = formatConfig.includeHeaders;

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Success Message */}
      <Card className="border-green-200 bg-green-50">
        <CardContent className="pt-6">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-6 w-6 text-green-600" />
            <div>
              <h3 className="font-semibold text-green-900">Conversione Completata!</h3>
              <p className="text-sm text-green-700">
                Il tuo CSV è pronto per il download con {totalRows} righe{' '}
                {hasHeaders && '(+ intestazioni)'} e {columns.length} colonne
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-3xl font-bold">{totalRows}</p>
              <p className="text-sm text-muted-foreground">Righe estratte</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-3xl font-bold">{columns.length}</p>
              <p className="text-sm text-muted-foreground">Colonne</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-3xl font-bold">{formatConfig.delimiter === '\t' ? 'TAB' : formatConfig.delimiter}</p>
              <p className="text-sm text-muted-foreground">Delimitatore</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Data Preview */}
      <Card>
        <CardHeader>
          <CardTitle>Anteprima Dati</CardTitle>
          <CardDescription>Prime 10 righe del CSV generato</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <div className="inline-block min-w-full align-middle">
              <div className="overflow-hidden border rounded-lg">
                <table className="min-w-full divide-y divide-border">
                  <thead className="bg-muted">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider w-12">
                        #
                      </th>
                      {columns.map((col) => (
                        <th
                          key={col.id}
                          className="px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider"
                        >
                          {col.outputName}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-background divide-y divide-border">
                    {data.slice(0, 10).map((row, rowIndex) => (
                      <tr key={rowIndex} className="hover:bg-muted/50">
                        <td className="px-3 py-2 text-xs text-muted-foreground">
                          {rowIndex + 1}
                        </td>
                        {row.map((cell, cellIndex) => (
                          <td key={cellIndex} className="px-3 py-2 text-sm whitespace-nowrap">
                            {cell || '-'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {totalRows > 10 && (
                <p className="text-xs text-muted-foreground mt-2 text-center">
                  ... e altre {totalRows - 10} righe
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Format Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Configurazione Formato</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Delimitatore:</span>
              <span className="ml-2 font-medium">
                {formatConfig.delimiter === '\t' ? 'Tab' : formatConfig.delimiter}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Separatore decimale:</span>
              <span className="ml-2 font-medium">{formatConfig.decimalSeparator}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Separatore migliaia:</span>
              <span className="ml-2 font-medium">
                {formatConfig.thousandsSeparator === 'none'
                  ? 'Nessuno'
                  : formatConfig.thousandsSeparator}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Formato data:</span>
              <span className="ml-2 font-medium">{formatConfig.dateFormat}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Encoding:</span>
              <span className="ml-2 font-medium">{formatConfig.encoding}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Intestazioni:</span>
              <span className="ml-2 font-medium">{hasHeaders ? 'Sì' : 'No'}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-between items-center">
        <Button variant="outline" onClick={onReset}>
          <FileText className="mr-2 h-4 w-4" />
          Nuova Conversione
        </Button>
        <Button onClick={onDownload} size="lg">
          <Download className="mr-2 h-5 w-5" />
          Scarica CSV
        </Button>
      </div>
    </div>
  );
}
