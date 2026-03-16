'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';
import type { FormatConfig as FormatConfigType } from '@/lib/types';

interface FormatConfigProps {
  config: FormatConfigType;
  onChange: (config: FormatConfigType) => void;
  onNext: () => void;
}

export function FormatConfig({ config, onChange, onNext }: FormatConfigProps) {
  const updateConfig = (key: keyof FormatConfigType, value: string | boolean) => {
    onChange({ ...config, [key]: value });
  };

  return (
    <div className="w-full max-w-3xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Configurazione Formato Output</CardTitle>
          <CardDescription>
            Definisci come vuoi che venga formattato il file CSV in output
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Delimiter */}
          <div className="space-y-2">
            <Label htmlFor="delimiter">Delimitatore Colonne</Label>
            <Select
              value={config.delimiter}
              onValueChange={(value) =>
                updateConfig('delimiter', value as FormatConfigType['delimiter'])
              }
            >
              <SelectTrigger id="delimiter">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value=",">Virgola (,)</SelectItem>
                <SelectItem value=";">Punto e virgola (;)</SelectItem>
                <SelectItem value="|">Pipe (|)</SelectItem>
                <SelectItem value="\t">Tab</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Carattere usato per separare le colonne nel CSV
            </p>
          </div>

          {/* Decimal Separator */}
          <div className="space-y-2">
            <Label htmlFor="decimal">Separatore Decimale</Label>
            <Select
              value={config.decimalSeparator}
              onValueChange={(value) =>
                updateConfig('decimalSeparator', value as FormatConfigType['decimalSeparator'])
              }
            >
              <SelectTrigger id="decimal">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value=",">Virgola (,) - Standard IT</SelectItem>
                <SelectItem value=".">Punto (.) - Standard US</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Come rappresentare i decimali nei numeri (es. 1,50 vs 1.50)
            </p>
          </div>

          {/* Thousands Separator */}
          <div className="space-y-2">
            <Label htmlFor="thousands">Separatore Migliaia</Label>
            <Select
              value={config.thousandsSeparator}
              onValueChange={(value) =>
                updateConfig('thousandsSeparator', value as FormatConfigType['thousandsSeparator'])
              }
            >
              <SelectTrigger id="thousands">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value=".">Punto (.)</SelectItem>
                <SelectItem value=",">Virgola (,)</SelectItem>
                <SelectItem value=" ">Spazio ( )</SelectItem>
                <SelectItem value="none">Nessuno</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Come separare le migliaia (es. 1.000 vs 1,000 vs 1000)
            </p>
          </div>

          {/* Date Format */}
          <div className="space-y-2">
            <Label htmlFor="dateFormat">Formato Data</Label>
            <Select
              value={config.dateFormat}
              onValueChange={(value) => updateConfig('dateFormat', value)}
            >
              <SelectTrigger id="dateFormat">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="DD/MM/YYYY">DD/MM/YYYY (31/12/2024)</SelectItem>
                <SelectItem value="MM/DD/YYYY">MM/DD/YYYY (12/31/2024)</SelectItem>
                <SelectItem value="YYYY-MM-DD">YYYY-MM-DD (2024-12-31)</SelectItem>
                <SelectItem value="DD-MM-YYYY">DD-MM-YYYY (31-12-2024)</SelectItem>
                <SelectItem value="DD.MM.YYYY">DD.MM.YYYY (31.12.2024)</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Formato per le colonne con date
            </p>
          </div>

          {/* Encoding */}
          <div className="space-y-2">
            <Label htmlFor="encoding">Encoding File</Label>
            <Select
              value={config.encoding}
              onValueChange={(value) =>
                updateConfig('encoding', value as FormatConfigType['encoding'])
              }
            >
              <SelectTrigger id="encoding">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="UTF-8">UTF-8 (Raccomandato)</SelectItem>
                <SelectItem value="ISO-8859-1">ISO-8859-1 (Latin-1)</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Encoding caratteri del file (UTF-8 supporta caratteri accentati)
            </p>
          </div>

          {/* Include Headers */}
          <div className="flex items-center justify-between space-x-2 rounded-lg border p-4">
            <div className="space-y-0.5">
              <Label htmlFor="headers" className="cursor-pointer">
                Includi Intestazioni
              </Label>
              <p className="text-xs text-muted-foreground">
                Aggiungi la riga con i nomi delle colonne come prima riga del CSV
              </p>
            </div>
            <Switch
              id="headers"
              checked={config.includeHeaders}
              onCheckedChange={(checked) => updateConfig('includeHeaders', checked)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Preview Format */}
      <Card>
        <CardHeader>
          <CardTitle>Anteprima Formato</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-muted p-4 rounded-lg font-mono text-sm">
            {config.includeHeaders && (
              <>
                <span>Data{config.delimiter}Descrizione{config.delimiter}Importo</span>
                <br />
              </>
            )}
            <span>
              01/01/2024{config.delimiter}Pagamento Fattura{config.delimiter}
              {config.thousandsSeparator === 'none' ? '1250' : `1${config.thousandsSeparator}250`}
              {config.decimalSeparator}00
            </span>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={onNext}>
          Genera CSV
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
