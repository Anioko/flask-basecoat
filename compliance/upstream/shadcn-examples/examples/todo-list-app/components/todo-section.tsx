import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { useDroppable } from "@dnd-kit/core";
import { Card } from "@/components/ui/card";
import { TodoItem } from "./todo-item";
import { MoreHorizontal, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { TodoSection as TodoSectionType } from "../types";

interface TodoSectionProps {
  section: TodoSectionType;
  onToggleTodo: (todoId: string) => void;
  isDraggedOver?: boolean;
}

export function TodoSection({ section, onToggleTodo, isDraggedOver = false }: TodoSectionProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: section.id
  });

  const getIcon = (iconName: string) => {
    switch (iconName) {
      case "📋":
        return "📋";
      case "⭐":
        return "⭐";
      case "⚡":
        return "⚡";
      default:
        return iconName;
    }
  };

  return (
    <Card
      className={cn(
        "bg-card border-0 p-4 shadow-sm transition-colors",
        (isOver || isDraggedOver) && "ring-primary/50 bg-primary/5 ring-2"
      )}>
      <div ref={setNodeRef} className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">{getIcon(section.icon)}</span>
            <h2 className="text-foreground font-semibold">{section.title}</h2>
          </div>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <Calendar className="text-muted-foreground h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <MoreHorizontal className="text-muted-foreground h-4 w-4" />
            </Button>
          </div>
        </div>

        <SortableContext
          items={section.todos.map((todo) => todo.id)}
          strategy={verticalListSortingStrategy}>
          <div
            className={cn(
              "min-h-[100px] space-y-2 rounded-md transition-colors",
              (isOver || isDraggedOver) &&
                section.todos.length === 0 &&
                "bg-primary/5 border-primary/30 border-2 border-dashed"
            )}>
            {section.todos.map((todo) => (
              <TodoItem key={todo.id} todo={todo} onToggle={() => onToggleTodo(todo.id)} />
            ))}
            {section.todos.length === 0 && (
              <div className="text-muted-foreground flex h-20 items-center justify-center text-sm">
                {isOver || isDraggedOver ? "Drop task here" : "No tasks"}
              </div>
            )}
          </div>
        </SortableContext>
      </div>
    </Card>
  );
}
