'use client';

import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { GripVertical, Type, Hash, Calendar, DollarSign } from 'lucide-react';
import type { SelectedColumn } from '@/lib/types';

interface SortableColumnItemProps {
  column: SelectedColumn & { selected?: boolean };
  onToggle: (columnId: string) => void;
  onNameChange: (columnId: string, newName: string) => void;
}

const columnTypeIcons = {
  text: Type,
  number: Hash,
  date: Calendar,
  currency: DollarSign,
};

export function SortableColumnItem({ column, onToggle, onNameChange }: SortableColumnItemProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: column.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const Icon = columnTypeIcons[column.type];
  const isSelected = column.selected !== false;

  return (
    <div ref={setNodeRef} style={style} {...attributes}>
      <Card className={`p-4 ${!isSelected ? 'opacity-50' : ''}`}>
        <div className="flex items-center gap-4">
          <button
            className="cursor-grab active:cursor-grabbing touch-none"
            {...listeners}
          >
            <GripVertical className="h-5 w-5 text-muted-foreground" />
          </button>

          <div className="flex items-center gap-2 min-w-[100px]">
            <Icon className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground capitalize">{column.type}</span>
          </div>

          <div className="flex-1 grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Nome originale</p>
              <p className="font-medium">{column.name}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Nome output</p>
              <Input
                value={column.outputName}
                onChange={(e) => onNameChange(column.id, e.target.value)}
                disabled={!isSelected}
                className="h-8"
              />
            </div>
          </div>

          <div className="flex flex-col items-center gap-1">
            <span className="text-xs text-muted-foreground">Confidence</span>
            <span className="text-sm font-medium">{Math.round(column.confidence * 100)}%</span>
          </div>

          <Switch checked={isSelected} onCheckedChange={() => onToggle(column.id)} />
        </div>

        {column.sampleData.length > 0 && isSelected && (
          <div className="mt-3 pl-9">
            <p className="text-xs text-muted-foreground mb-1">Dati esempio:</p>
            <div className="flex gap-2 flex-wrap">
              {column.sampleData.slice(0, 3).map((sample, idx) => (
                <span key={idx} className="text-xs bg-muted px-2 py-1 rounded">
                  {sample}
                </span>
              ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
