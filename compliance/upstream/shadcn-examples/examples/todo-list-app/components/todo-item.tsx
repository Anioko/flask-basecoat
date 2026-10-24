import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { MessageCircle, GripVertical } from "lucide-react";
import { cn } from "@/lib/utils";
import { Todo } from "@/examples/todo-list-app/types";

interface TodoItemProps {
  todo: Todo;
  onToggle: () => void;
}

export function TodoItem({ todo, onToggle }: TodoItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    setActivatorNodeRef,
    transform,
    transition,
    isDragging
  } = useSortable({ id: todo.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition
  };

  const getPriorityBadgeVariant = (priority: string) => {
    switch (priority) {
      case "important":
        return "bg-todo-important/10 text-todo-important hover:bg-todo-important/20";
      case "new-product":
        return "bg-todo-new-product/10 text-todo-new-product hover:bg-todo-new-product/20";
      case "delayed":
        return "bg-todo-delayed/10 text-todo-delayed hover:bg-todo-delayed/20";
      default:
        return "secondary";
    }
  };

  const getPriorityText = (priority: string) => {
    switch (priority) {
      case "important":
        return "Important";
      case "new-product":
        return "New product";
      case "delayed":
        return "Delayed";
      default:
        return priority;
    }
  };

  const getProgressColor = (progress: number) => {
    if (progress >= 80) return "text-todo-success";
    if (progress >= 50) return "text-todo-new-product";
    if (progress >= 20) return "text-todo-progress";
    return "text-todo-delayed";
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        "bg-background border-border/50 hover:border-border flex items-center gap-3 rounded-lg border p-3 transition-all",
        isDragging && "opacity-50"
      )}>
      <Button
        ref={setActivatorNodeRef}
        variant="ghost"
        size="icon"
        className="text-muted-foreground hover:text-foreground h-6 w-6 cursor-grab active:cursor-grabbing"
        {...attributes}
        {...listeners}>
        <GripVertical className="h-3 w-3" />
      </Button>

      <Checkbox checked={todo.completed} onCheckedChange={onToggle} />

      <div className="min-w-0 flex-1">
        <p
          className={cn(
            "text-sm font-medium",
            todo.completed && "text-muted-foreground line-through"
          )}>
          {todo.text}
        </p>
      </div>

      <div className="flex items-center gap-2">
        {todo.priority && (
          <Badge
            variant="secondary"
            className={cn("border-0 text-xs font-medium", getPriorityBadgeVariant(todo.priority))}>
            {getPriorityText(todo.priority)}
          </Badge>
        )}

        {todo.progress !== undefined && (
          <div className="flex items-center gap-1">
            <div
              className={cn(
                "flex h-4 w-4 items-center justify-center rounded-full border-2",
                getProgressColor(todo.progress)
              )}>
              <div className="h-2 w-2 rounded-full bg-current" />
            </div>
            <span className={cn("text-xs font-medium", getProgressColor(todo.progress))}>
              {todo.progress}%
            </span>
          </div>
        )}

        {todo.comments && (
          <div className="text-muted-foreground flex items-center gap-1">
            <MessageCircle className="h-3 w-3" />
            <span className="text-xs">{todo.comments}</span>
          </div>
        )}

        <div className="flex -space-x-1">
          <Avatar className="border-background h-6 w-6 border">
            <AvatarImage src={todo.avatar} />
            <AvatarFallback className="bg-todo-progress text-xs text-white">
              {todo.avatar ? todo.avatar[0].toUpperCase() : "JM"}
            </AvatarFallback>
          </Avatar>
          <div className="bg-muted border-background flex h-6 w-6 items-center justify-center rounded-full border">
            <span className="text-muted-foreground text-xs">+3</span>
          </div>
        </div>
      </div>
    </div>
  );
}
