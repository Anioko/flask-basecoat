"use client";

import { useState } from "react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
  DragOverEvent
} from "@dnd-kit/core";
import { arrayMove, sortableKeyboardCoordinates } from "@dnd-kit/sortable";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, Bell, Plus } from "lucide-react";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { TodoSection as TodoSectionType } from "./types";
import { TodoSection } from "@/examples/todo-list-app/components/todo-section";

const initialSections: TodoSectionType[] = [
  {
    id: "new-tasks",
    title: "New tasks",
    icon: "📋",
    todos: [
      {
        id: "1",
        text: "Get another day full of work done!",
        completed: false,
        priority: "important",
        progress: 74,
        comments: 18,
        avatar: "/avatars/jm.jpg"
      },
      {
        id: "2",
        text: "Keep my mentality healthy by taking walks outside",
        completed: true,
        progress: 38,
        comments: 18,
        avatar: "/avatars/jm.jpg"
      }
    ]
  },
  {
    id: "do-today",
    title: "Do today",
    icon: "⭐",
    todos: [
      {
        id: "3",
        text: "Figure out how to use Clever from the help center!",
        completed: true,
        progress: 10,
        comments: 18,
        avatar: "/avatars/jm.jpg"
      },
      {
        id: "4",
        text: "Build some new components in Figma",
        completed: false,
        priority: "new-product",
        progress: 83,
        comments: 18,
        avatar: "/avatars/jm.jpg"
      },
      {
        id: "5",
        text: "Create wireframes for the new dashboard",
        completed: true,
        priority: "delayed",
        progress: 4,
        comments: 18,
        avatar: "/avatars/jm.jpg"
      }
    ]
  },
  {
    id: "in-progress",
    title: "In progress",
    icon: "⚡",
    todos: [
      {
        id: "6",
        text: "Figure out how to use Clever from the help center!",
        completed: false,
        progress: 10,
        comments: 18,
        avatar: "/avatars/jm.jpg"
      },
      {
        id: "7",
        text: "Build some new components in Figma",
        completed: false,
        priority: "delayed",
        progress: 83,
        comments: 18,
        avatar: "/avatars/jm.jpg"
      },
      {
        id: "8",
        text: "Create wireframes for the new dashboard",
        completed: true,
        priority: "delayed",
        progress: 4,
        comments: 18,
        avatar: "/avatars/jm.jpg"
      },
      {
        id: "9",
        text: "Get another day full of work done!",
        completed: true,
        progress: 74,
        comments: 18,
        avatar: "/avatars/jm.jpg"
      },
      {
        id: "10",
        text: "Keep my mentality healthy by taking walks outside",
        completed: false,
        progress: 38,
        comments: 18,
        avatar: "/avatars/jm.jpg"
      }
    ]
  }
];

export default function Page() {
  const [sections, setSections] = useState<TodoSectionType[]>(initialSections);
  const [dragOverContainer, setDragOverContainer] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates
    })
  );

  const handleDragOver = (event: DragOverEvent) => {
    const { over } = event;

    if (!over) {
      setDragOverContainer(null);
      return;
    }

    const overId = over.id as string;

    // Check if we're over a section directly
    const overSection = sections.find((s) => s.id === overId);
    if (overSection) {
      setDragOverContainer(overId);
      return;
    }

    // Check if we're over a todo item, find its container
    sections.forEach((section) => {
      const overIdx = section.todos.findIndex((todo) => todo.id === overId);
      if (overIdx !== -1) {
        setDragOverContainer(section.id);
      }
    });
  };

  const handleDragStart = () => {
    setDragOverContainer(null);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    setDragOverContainer(null);

    const { active, over } = event;

    if (!over) return;

    const activeId = active.id as string;
    const overId = over.id as string;

    // Find the active item and its container
    let activeContainer = "";
    let activeIndex = -1;

    sections.forEach((section) => {
      const activeIdx = section.todos.findIndex((todo) => todo.id === activeId);
      if (activeIdx !== -1) {
        activeContainer = section.id;
        activeIndex = activeIdx;
      }
    });

    // Check if we're dropping over a section or a todo item
    let overContainer = "";
    let overIndex = -1;

    // First check if we're dropping over a section directly
    const overSection = sections.find((s) => s.id === overId);
    if (overSection) {
      overContainer = overId;
      overIndex = overSection.todos.length; // Add to the end
    } else {
      // We're dropping over a todo item
      sections.forEach((section) => {
        const overIdx = section.todos.findIndex((todo) => todo.id === overId);
        if (overIdx !== -1) {
          overContainer = section.id;
          overIndex = overIdx;
        }
      });
    }

    if (activeContainer && overContainer && activeId !== overId) {
      setSections((prevSections) => {
        const newSections = [...prevSections];
        const activeSection = newSections.find((s) => s.id === activeContainer)!;
        const overSection = newSections.find((s) => s.id === overContainer)!;

        if (activeContainer === overContainer) {
          // Same container - reorder
          activeSection.todos = arrayMove(activeSection.todos, activeIndex, overIndex);
        } else {
          // Different containers - move between sections
          const [movedTodo] = activeSection.todos.splice(activeIndex, 1);
          overSection.todos.splice(overIndex, 0, movedTodo);
        }

        return newSections;
      });
    }
  };

  const handleToggleTodo = (todoId: string) => {
    setSections((prevSections) =>
      prevSections.map((section) => ({
        ...section,
        todos: section.todos.map((todo) =>
          todo.id === todoId ? { ...todo, completed: !todo.completed } : todo
        )
      }))
    );
  };

  return (
    <div className="bg-background min-h-screen">
      <div className="mx-auto max-w-7xl p-4 md:p-6">
        {/* Header */}
        <div className="mb-8">
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1">
                <div className="flex h-8 w-8 items-center justify-center rounded-md bg-pink-100">
                  <span className="text-sm font-semibold text-pink-600">C</span>
                </div>
                <div className="flex h-8 w-8 items-center justify-center rounded-md bg-blue-100">
                  <span className="text-sm font-semibold text-blue-600">D</span>
                </div>
                <div className="flex h-8 w-8 items-center justify-center rounded-md bg-orange-100">
                  <span className="text-sm font-semibold text-orange-600">A</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="border-border h-8 w-8 border border-dashed p-0">
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="relative">
                <Search className="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 transform" />
                <Input placeholder="Search" className="bg-background border-border w-64 pl-10" />
              </div>
              <Button variant="ghost" size="sm" className="h-9 w-9 p-0">
                <Bell className="h-4 w-4" />
              </Button>
              <Avatar className="h-8 w-8">
                <AvatarImage src="/avatars/tahlia.jpg" />
                <AvatarFallback className="bg-orange-500 text-sm text-white">T</AvatarFallback>
              </Avatar>
            </div>
          </div>

          <div className="mb-6">
            <h1 className="text-foreground mb-4 text-2xl font-bold">
              Launch Clever dashboard theme
            </h1>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <Button className="rounded-full" size="sm">
                  View all
                </Button>
                <Button variant="outline" className="rounded-full" size="sm">
                  Most recent
                </Button>
                <Button variant="outline" className="rounded-full" size="sm">
                  Popular
                </Button>
              </div>
              <div className="ml-auto flex items-center gap-2">
                <Button variant="outline" size="sm">
                  Share
                </Button>
                <Button size="sm" className="bg-primary hover:bg-primary/90">
                  Create
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Todo Sections */}
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragEnd={handleDragEnd}>
          <div className="space-y-6">
            {sections.map((section) => (
              <TodoSection
                key={section.id}
                section={section}
                onToggleTodo={handleToggleTodo}
                isDraggedOver={dragOverContainer === section.id}
              />
            ))}
          </div>
        </DndContext>
      </div>
    </div>
  );
}
