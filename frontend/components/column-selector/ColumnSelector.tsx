'use client';

import { useState, useEffect } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { DetectedColumn, SelectedColumn } from '@/lib/types';
import { SortableColumnItem } from './SortableColumnItem';
import { ArrowRight } from 'lucide-react';

interface ColumnSelectorProps {
  detectedColumns: DetectedColumn[];
  onColumnsSelected: (columns: SelectedColumn[]) => void;
  onNext: () => void;
}

export function ColumnSelector({
  detectedColumns,
  onColumnsSelected,
  onNext,
}: ColumnSelectorProps) {
  const [selectedColumns, setSelectedColumns] = useState<SelectedColumn[]>(() =>
    detectedColumns.map((col, index) => ({
      ...col,
      order: index,
      outputName: col.name,
    }))
  );

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Notify parent when columns change
  useEffect(() => {
    const visibleCols = selectedColumns.filter(
      (col) => (col as { selected?: boolean }).selected !== false
    );
    onColumnsSelected(visibleCols);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedColumns]); // Only depend on selectedColumns, not onColumnsSelected

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      setSelectedColumns((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id);
        const newIndex = items.findIndex((item) => item.id === over.id);
        const reordered = arrayMove(items, oldIndex, newIndex);
        const updated = reordered.map((col, index) => ({ ...col, order: index }));
        return updated;
      });
    }
  };

  const toggleColumn = (columnId: string) => {
    setSelectedColumns((prev) => {
      const column = prev.find((col) => col.id === columnId);
      if (!column) return prev;

      // Toggle visibility by adding/removing a selected flag
      const updated = prev.map((col) =>
        col.id === columnId ? { ...col, selected: !col.selected } : col
      ) as (SelectedColumn & { selected?: boolean })[];

      return updated as SelectedColumn[];
    });
  };

  const updateColumnName = (columnId: string, newName: string) => {
    setSelectedColumns((prev) => {
      const updated = prev.map((col) =>
        col.id === columnId ? { ...col, outputName: newName } : col
      );
      return updated;
    });
  };

  const visibleColumns = selectedColumns.filter(
    (col) => (col as { selected?: boolean }).selected !== false
  );

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Colonne Rilevate</CardTitle>
          <CardDescription>
            Seleziona le colonne da estrarre e riordinale trascinandole. Puoi anche rinominare le
            intestazioni.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
            <SortableContext
              items={selectedColumns.map((col) => col.id)}
              strategy={verticalListSortingStrategy}
            >
              <div className="space-y-2">
                {selectedColumns.map((column) => (
                  <SortableColumnItem
                    key={column.id}
                    column={column}
                    onToggle={toggleColumn}
                    onNameChange={updateColumnName}
                  />
                ))}
              </div>
            </SortableContext>
          </DndContext>

          {selectedColumns.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              Nessuna colonna rilevata. Riprova con un altro documento.
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-between items-center">
        <p className="text-sm text-muted-foreground">
          {visibleColumns.length} di {selectedColumns.length} colonne selezionate
        </p>
        <Button onClick={onNext} disabled={visibleColumns.length === 0}>
          Continua
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
