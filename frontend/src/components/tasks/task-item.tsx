"use client";

import { useState, useMemo } from "react";
import type { Task, Priority } from "@/lib/types";

interface TaskItemProps {
  task: Task;
  onToggle: (id: string) => void;
  onEdit?: (task: Task) => void;
  onDelete?: (id: string) => void;
}

const priorityConfig: Record<Priority, { label: string; color: string; bg: string }> = {
  high: { label: "High", color: "text-red-700", bg: "bg-red-100" },
  medium: { label: "Med", color: "text-yellow-700", bg: "bg-yellow-100" },
  low: { label: "Low", color: "text-green-700", bg: "bg-green-100" },
};

/**
 * Individual task item component.
 * Per FR-011a: Display completed tasks with visual distinction.
 */
export function TaskItem({ task, onToggle, onEdit, onDelete }: TaskItemProps) {
  const [isToggling, setIsToggling] = useState(false);

  const dueInfo = useMemo(() => {
    if (!task.dueDate) return null;
    const due = new Date(task.dueDate);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    due.setHours(0, 0, 0, 0);
    const diffDays = Math.ceil((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays < 0 && !task.completed) {
      return { label: "Overdue", isOverdue: true, isToday: false };
    } else if (diffDays === 0) {
      return { label: "Today", isOverdue: false, isToday: true };
    } else if (diffDays === 1) {
      return { label: "Tomorrow", isOverdue: false, isToday: false };
    } else {
      return {
        label: due.toLocaleDateString(undefined, { month: "short", day: "numeric" }),
        isOverdue: false,
        isToday: false,
      };
    }
  }, [task.dueDate, task.completed]);

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

        {/* Priority badge and Due date */}
        <div className="mt-2 flex items-center gap-2 flex-wrap">
          {task.priority && task.priority !== "medium" && (
            <span
              className={`
                inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
                ${priorityConfig[task.priority]?.bg || "bg-gray-100"}
                ${priorityConfig[task.priority]?.color || "text-gray-700"}
              `}
            >
              {priorityConfig[task.priority]?.label || task.priority}
            </span>
          )}

          {dueInfo && (
            <span
              className={`
                inline-flex items-center gap-1 text-xs
                ${dueInfo.isOverdue ? "text-red-600 font-medium" : ""}
                ${dueInfo.isToday ? "text-blue-600 font-medium" : ""}
                ${!dueInfo.isOverdue && !dueInfo.isToday ? "text-gray-500" : ""}
              `}
            >
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              {dueInfo.label}
            </span>
          )}

          {/* Timestamp */}
          <span className="text-xs text-gray-400">
            {task.completed ? "Completed" : "Created"} {(() => {
              const dateStr = task.createdAt || (task as unknown as { created_at?: string }).created_at;
              if (!dateStr) return "";
              const date = new Date(dateStr);
              const currentYear = new Date().getFullYear().toString();
              return date.toLocaleDateString(undefined, {
                month: "short",
                day: "numeric",
                year: dateStr.startsWith(currentYear) ? undefined : "numeric"
              });
            })()}
          </span>
        </div>
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
