'use client';

import { useCallback, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Upload, File, X } from 'lucide-react';
import type { UploadedDocument } from '@/lib/types';

interface FileUploadProps {
  onFileUpload: (document: UploadedDocument) => void;
  isProcessing?: boolean;
}

export function FileUpload({ onFileUpload, isProcessing = false }: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<UploadedDocument | null>(null);

  const handleFile = useCallback(
    (file: File) => {
      if (!file) return;

      const fileType = file.type.includes('pdf') ? 'pdf' : 'image';
      const preview = URL.createObjectURL(file);

      const document: UploadedDocument = {
        id: crypto.randomUUID(),
        file,
        preview,
        type: fileType,
      };

      setUploadedFile(document);
      onFileUpload(document);
    },
    [onFileUpload]
  );

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFile(e.dataTransfer.files[0]);
      }
    },
    [handleFile]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      e.preventDefault();
      if (e.target.files && e.target.files[0]) {
        handleFile(e.target.files[0]);
      }
    },
    [handleFile]
  );

  const handleRemove = useCallback(() => {
    if (uploadedFile) {
      URL.revokeObjectURL(uploadedFile.preview);
      setUploadedFile(null);
    }
  }, [uploadedFile]);

  return (
    <div className="w-full max-w-2xl mx-auto">
      {!uploadedFile ? (
        <Card
          className={`relative p-12 border-2 border-dashed transition-colors ${
            dragActive
              ? 'border-primary bg-primary/5'
              : 'border-muted-foreground/25 hover:border-primary/50'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="file-upload"
            className="hidden"
            accept=".pdf,.jpg,.jpeg,.png,.tiff"
            onChange={handleChange}
            disabled={isProcessing}
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <div className="flex flex-col items-center justify-center gap-4 text-center">
              <div className="rounded-full bg-primary/10 p-4">
                <Upload className="h-8 w-8 text-primary" />
              </div>
              <div>
                <p className="text-lg font-semibold">
                  Trascina il documento qui o clicca per caricare
                </p>
                <p className="text-sm text-muted-foreground mt-2">
                  Supportati: PDF, JPG, PNG, TIFF (max 20MB)
                </p>
              </div>
              <Button type="button" disabled={isProcessing}>
                Seleziona File
              </Button>
            </div>
          </label>
        </Card>
      ) : (
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-primary/10 p-3">
                <File className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="font-medium">{uploadedFile.file.name}</p>
                <p className="text-sm text-muted-foreground">
                  {(uploadedFile.file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleRemove}
              disabled={isProcessing}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
