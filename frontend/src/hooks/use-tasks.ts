"use client";

/**
 * Task Management Hook with Real-Time Sync Support.
 *
 * Per T045: Integrates with useRealTimeSync to automatically update
 * task list when changes occur on other devices/tabs.
 */

import { useState, useEffect, useCallback } from "react";
import { taskApi } from "@/lib/api.client";
import { useRealTimeSync, ConnectionStatus } from "@/hooks/useRealTimeSync";
import type { Task, TaskCreate, TaskUpdate } from "@/lib/types";

export type SortBy = "created_at" | "due_date";

interface UseTasksOptions {
  sortBy?: SortBy;
  /** Authentication token for real-time sync */
  token?: string | null;
  /** Enable real-time sync (default: true if token provided) */
  enableRealTimeSync?: boolean;
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
  /** Real-time sync connection status */
  syncStatus: ConnectionStatus;
  /** Whether real-time sync is connected */
  isSyncing: boolean;
}

/**
 * Hook for managing task data with real-time synchronization.
 *
 * Features:
 * - CRUD operations with optimistic updates
 * - Real-time sync via WebSocket (Phase V)
 * - Connection status tracking
 * - Automatic task list updates from other devices/tabs
 */
export function useTasks(options: UseTasksOptions = {}): UseTasksReturn {
  const { sortBy = "created_at", token = null, enableRealTimeSync = true } = options;
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Track task IDs that were just modified locally to avoid duplicate updates
  const [recentLocalChanges, setRecentLocalChanges] = useState<Set<string>>(new Set());

  // Real-time sync handlers
  const handleRemoteTaskCreated = useCallback((task: Task) => {
    // Skip if this was a local change
    if (recentLocalChanges.has(task.id)) {
      setRecentLocalChanges((prev) => {
        const next = new Set(prev);
        next.delete(task.id);
        return next;
      });
      return;
    }

    // Add to beginning of list (newest first)
    setTasks((prev) => {
      // Check if task already exists (avoid duplicates)
      if (prev.some((t) => t.id === task.id)) {
        return prev;
      }
      return [task, ...prev];
    });
  }, [recentLocalChanges]);

  const handleRemoteTaskUpdated = useCallback((task: Task) => {
    // Skip if this was a local change
    if (recentLocalChanges.has(task.id)) {
      setRecentLocalChanges((prev) => {
        const next = new Set(prev);
        next.delete(task.id);
        return next;
      });
      return;
    }

    setTasks((prev) => prev.map((t) => (t.id === task.id ? task : t)));
  }, [recentLocalChanges]);

  const handleRemoteTaskDeleted = useCallback((taskId: string) => {
    // Skip if this was a local change
    if (recentLocalChanges.has(taskId)) {
      setRecentLocalChanges((prev) => {
        const next = new Set(prev);
        next.delete(taskId);
        return next;
      });
      return;
    }

    setTasks((prev) => prev.filter((t) => t.id !== taskId));
  }, [recentLocalChanges]);

  // Initialize real-time sync
  const { status: syncStatus, isConnected: isSyncing } = useRealTimeSync({
    token: enableRealTimeSync ? token : null,
    enabled: enableRealTimeSync && !!token,
    onTaskCreated: handleRemoteTaskCreated,
    onTaskUpdated: handleRemoteTaskUpdated,
    onTaskDeleted: handleRemoteTaskDeleted,
  });

  // Fetch tasks from API
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

  // Mark a task ID as recently changed locally
  const markLocalChange = useCallback((taskId: string) => {
    setRecentLocalChanges((prev) => new Set(prev).add(taskId));
    // Clear after 5 seconds
    setTimeout(() => {
      setRecentLocalChanges((prev) => {
        const next = new Set(prev);
        next.delete(taskId);
        return next;
      });
    }, 5000);
  }, []);

  const createTask = useCallback(async (data: TaskCreate): Promise<Task | null> => {
    try {
      const task = await taskApi.createTask(data);
      markLocalChange(task.id);
      // Add to beginning of list (newest first)
      setTasks((prev) => [task, ...prev]);
      return task;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create task");
      return null;
    }
  }, [markLocalChange]);

  const updateTask = useCallback(async (id: string, data: TaskUpdate): Promise<Task | null> => {
    try {
      markLocalChange(id);
      const task = await taskApi.updateTask(id, data);
      setTasks((prev) => prev.map((t) => (t.id === id ? task : t)));
      return task;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update task");
      return null;
    }
  }, [markLocalChange]);

  const toggleTask = useCallback(async (id: string): Promise<Task | null> => {
    markLocalChange(id);

    // Optimistic update
    setTasks((prev) =>
      prev.map((t) => (t.id === id ? { ...t, completed: !t.completed } : t))
    );

    try {
      const task = await taskApi.toggleTask(id);
      // Update with actual server response
      setTasks((prev) => prev.map((t) => (t.id === id ? task : t)));
      return task;
    } catch (err) {
      // Revert optimistic update on error
      setTasks((prev) =>
        prev.map((t) => (t.id === id ? { ...t, completed: !t.completed } : t))
      );
      setError(err instanceof Error ? err.message : "Failed to toggle task");
      return null;
    }
  }, [markLocalChange]);

  const deleteTask = useCallback(async (id: string): Promise<boolean> => {
    try {
      markLocalChange(id);
      await taskApi.deleteTask(id);
      setTasks((prev) => prev.filter((t) => t.id !== id));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete task");
      return false;
    }
  }, [markLocalChange]);

  return {
    tasks,
    isLoading,
    error,
    createTask,
    updateTask,
    toggleTask,
    deleteTask,
    refetch: fetchTasks,
    syncStatus,
    isSyncing,
  };
}
