"use client";

import type { Task } from "@/lib/types";
import { TaskItem } from "./task-item";
import { Button } from "@/components/ui/button";

interface TaskListProps {
  tasks: Task[];
  isLoading: boolean;
  onToggle: (id: string) => void;
  onEdit?: (task: Task) => void;
  onDelete?: (id: string) => void;
  emptyMessage?: string;
  onAddTask?: () => void;
}

/**
 * Task list component with empty state.
 * Per spec US3: Display all tasks with status indicators.
 */
export function TaskList({
  tasks,
  isLoading,
  onToggle,
  onEdit,
  onDelete,
  emptyMessage,
  onAddTask,
}: TaskListProps) {
  // Loading state
  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8">
        <div className="flex flex-col items-center justify-center">
          <div className="relative">
            <div className="w-12 h-12 border-4 border-blue-100 rounded-full"></div>
            <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin absolute top-0 left-0"></div>
          </div>
          <p className="mt-4 text-gray-600 font-medium">Loading your tasks...</p>
          <p className="mt-1 text-sm text-gray-400">Just a moment</p>
        </div>
      </div>
    );
  }

  // Empty state
  if (tasks.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
        <div className="mx-auto w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mb-4">
          <svg
            className="h-8 w-8 text-blue-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
            />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900">
          {emptyMessage ? "No tasks here" : "No tasks yet"}
        </h3>
        <p className="mt-2 text-gray-500 max-w-sm mx-auto">
          {emptyMessage || "Get started by creating your first task. Stay organized and productive!"}
        </p>
        {onAddTask && !emptyMessage && (
          <Button onClick={onAddTask} className="mt-6">
            <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create Your First Task
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {tasks.map((task, index) => (
        <div
          key={task.id}
          className="animate-in fade-in slide-in-from-bottom-2 duration-300"
          style={{ animationDelay: `${index * 50}ms` }}
        >
          <TaskItem
            task={task}
            onToggle={onToggle}
            onEdit={onEdit}
            onDelete={onDelete}
          />
        </div>
      ))}
    </div>
  );
}
