export interface Todo {
  id: string;
  text: string;
  completed: boolean;
  priority?: "important" | "new-product" | "delayed";
  progress?: number;
  comments?: number;
  avatar?: string;
}

export interface TodoSection {
  id: string;
  title: string;
  icon: string;
  todos: Todo[];
}
