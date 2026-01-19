"use client";

import { useState, useEffect, useCallback } from "react";
import { taskApi } from "@/lib/api.client";
import type { Task, TaskCreate, TaskUpdate } from "@/lib/types";

export type SortBy = "created_at" | "due_date";

interface UseTasksOptions {
  sortBy?: SortBy;
}

interface UseTasksReturn {
  tasks: Task[];
  isLoading: boolean;
  error: string | null;
  createTask: (data: TaskCreate) => Promise<Task | null>;
  updateTask: (id: string, data: TaskUpdate) => Promise<Task | null>;
  toggleTask: (id: string) => Promise<Task | null>;
  deleteTask: (id: string) => Promise<boolean>;
  refetch: () => Promise<void>;
}

/**
 * Hook for managing task data and operations.
 * Per FR-010: Display loading states during API operations.
 */
export function useTasks(options: UseTasksOptions = {}): UseTasksReturn {
  const { sortBy = "created_at" } = options;
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await taskApi.listTasks(sortBy);
      setTasks(response.tasks);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch tasks");
    } finally {
      setIsLoading(false);
    }
  }, [sortBy]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const createTask = useCallback(async (data: TaskCreate): Promise<Task | null> => {
    try {
      const task = await taskApi.createTask(data);
      // Add to beginning of list (newest first)
      setTasks((prev) => [task, ...prev]);
      return task;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create task");
      return null;
    }
  }, []);

  const updateTask = useCallback(async (id: string, data: TaskUpdate): Promise<Task | null> => {
    try {
      const task = await taskApi.updateTask(id, data);
      setTasks((prev) =>
        prev.map((t) => (t.id === id ? task : t))
      );
      return task;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update task");
      return null;
    }
  }, []);

  const toggleTask = useCallback(async (id: string): Promise<Task | null> => {
    // Optimistic update (T065)
    setTasks((prev) =>
      prev.map((t) =>
        t.id === id ? { ...t, completed: !t.completed } : t
      )
    );

    try {
      const task = await taskApi.toggleTask(id);
      // Update with actual server response
      setTasks((prev) =>
        prev.map((t) => (t.id === id ? task : t))
      );
      return task;
    } catch (err) {
      // Revert optimistic update on error
      setTasks((prev) =>
        prev.map((t) =>
          t.id === id ? { ...t, completed: !t.completed } : t
        )
      );
      setError(err instanceof Error ? err.message : "Failed to toggle task");
      return null;
    }
  }, []);

  const deleteTask = useCallback(async (id: string): Promise<boolean> => {
    try {
      await taskApi.deleteTask(id);
      setTasks((prev) => prev.filter((t) => t.id !== id));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete task");
      return false;
    }
  }, []);

  return {
    tasks,
    isLoading,
    error,
    createTask,
    updateTask,
    toggleTask,
    deleteTask,
    refetch: fetchTasks,
  };
}
