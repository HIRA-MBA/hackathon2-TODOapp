"use client";

import { useState } from "react";
import type { Task } from "@/lib/types";

interface TaskItemProps {
  task: Task;
  onToggle: (id: string) => void;
  onEdit?: (task: Task) => void;
  onDelete?: (id: string) => void;
}

/**
 * Individual task item component.
 * Per FR-011a: Display completed tasks with visual distinction.
 */
export function TaskItem({ task, onToggle, onEdit, onDelete }: TaskItemProps) {
  const [isToggling, setIsToggling] = useState(false);

  const handleToggle = async () => {
    setIsToggling(true);
    await onToggle(task.id);
    setIsToggling(false);
  };

  return (
    <div
      className={`
        group flex items-start gap-4 p-4 bg-white rounded-xl border transition-all duration-200
        hover:shadow-md
        ${task.completed
          ? "border-gray-100 bg-gray-50/50"
          : "border-gray-200 hover:border-blue-200"
        }
      `}
    >
      {/* Custom Checkbox */}
      <button
        onClick={handleToggle}
        disabled={isToggling}
        className={`
          mt-0.5 flex-shrink-0 w-6 h-6 rounded-full border-2 transition-all duration-200
          flex items-center justify-center
          ${isToggling ? "opacity-50" : ""}
          ${task.completed
            ? "bg-green-500 border-green-500 text-white"
            : "border-gray-300 hover:border-blue-500 hover:bg-blue-50"
          }
        `}
        aria-label={`Mark "${task.title}" as ${task.completed ? "incomplete" : "complete"}`}
      >
        {task.completed && (
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        )}
      </button>

      {/* Task content */}
      <div className="flex-1 min-w-0">
        <h3
          className={`
            text-base font-medium leading-snug transition-colors
            ${task.completed ? "text-gray-400 line-through" : "text-gray-900"}
          `}
        >
          {task.title}
        </h3>

        {task.description && (
          <p
            className={`
              mt-1 text-sm leading-relaxed
              ${task.completed ? "text-gray-400" : "text-gray-500"}
            `}
          >
            {task.description}
          </p>
        )}

        {/* Timestamp */}
        <p className="mt-2 text-xs text-gray-400">
          {task.completed ? "Completed" : "Created"} {new Date(task.created_at).toLocaleDateString(undefined, {
            month: "short",
            day: "numeric",
            year: task.created_at.startsWith(new Date().getFullYear().toString()) ? undefined : "numeric"
          })}
        </p>
      </div>

      {/* Action buttons - visible on hover or focus */}
      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity">
        {onEdit && (
          <button
            onClick={() => onEdit(task)}
            className="p-2 rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
            aria-label={`Edit "${task.title}"`}
            title="Edit task"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
              />
            </svg>
          </button>
        )}

        {onDelete && (
          <button
            onClick={() => onDelete(task.id)}
            className="p-2 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
            aria-label={`Delete "${task.title}"`}
            title="Delete task"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
