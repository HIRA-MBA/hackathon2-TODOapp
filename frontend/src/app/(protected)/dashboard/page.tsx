"use client";

import { useState, useMemo } from "react";
import { useTasks } from "@/hooks/use-tasks";
import { TaskList } from "@/components/tasks/task-list";
import { TaskForm } from "@/components/tasks/task-form";
import { TaskEditDialog } from "@/components/tasks/task-edit-dialog";
import { Navbar } from "@/components/navbar";
import { Button } from "@/components/ui/button";
import type { Task } from "@/lib/types";

type FilterType = "all" | "active" | "completed";

/**
 * Dashboard page - main task management view.
 * Per FR-003: Protected dashboard page at /dashboard path.
 */
export default function DashboardPage() {
  const { tasks, isLoading, error, createTask, updateTask, toggleTask, deleteTask } = useTasks();
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [filter, setFilter] = useState<FilterType>("all");

  // Calculate task statistics
  const stats = useMemo(() => {
    const total = tasks.length;
    const completed = tasks.filter(t => t.completed).length;
    const active = total - completed;
    return { total, completed, active };
  }, [tasks]);

  // Filter tasks based on current filter
  const filteredTasks = useMemo(() => {
    switch (filter) {
      case "active":
        return tasks.filter(t => !t.completed);
      case "completed":
        return tasks.filter(t => t.completed);
      default:
        return tasks;
    }
  }, [tasks, filter]);

  const handleEdit = (task: Task) => {
    setEditingTask(task);
  };

  const handleDelete = (id: string) => {
    setShowDeleteConfirm(id);
  };

  const confirmDelete = async () => {
    if (showDeleteConfirm) {
      await deleteTask(showDeleteConfirm);
      setShowDeleteConfirm(null);
    }
  };

  const handleTaskCreated = async (data: { title: string; description: string | null }) => {
    const result = await createTask(data);
    if (result) {
      setShowAddForm(false);
    }
    return result;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <Navbar />

      <main className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Header with stats */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">My Tasks</h1>
              <p className="mt-1 text-gray-500">
                Stay organized and get things done
              </p>
            </div>

            {/* Quick Stats */}
            {!isLoading && tasks.length > 0 && (
              <div className="hidden sm:flex items-center gap-4">
                <div className="text-center px-4 py-2 bg-white rounded-lg shadow-sm">
                  <p className="text-2xl font-bold text-blue-600">{stats.active}</p>
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Active</p>
                </div>
                <div className="text-center px-4 py-2 bg-white rounded-lg shadow-sm">
                  <p className="text-2xl font-bold text-green-600">{stats.completed}</p>
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Done</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Error display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <svg className="h-5 w-5 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Action Bar */}
        <div className="mb-6 flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          {/* Add Task Button */}
          {!showAddForm && (
            <Button
              onClick={() => setShowAddForm(true)}
              className="flex items-center gap-2 shadow-lg hover:shadow-xl transition-shadow"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add New Task
            </Button>
          )}

          {/* Filter Tabs */}
          {tasks.length > 0 && (
            <div className="flex bg-white rounded-lg p-1 shadow-sm border border-gray-200">
              {(["all", "active", "completed"] as FilterType[]).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`
                    px-4 py-2 text-sm font-medium rounded-md transition-colors
                    ${filter === f
                      ? "bg-blue-600 text-white shadow-sm"
                      : "text-gray-600 hover:bg-gray-100"
                    }
                  `}
                >
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                  {f === "all" && ` (${stats.total})`}
                  {f === "active" && ` (${stats.active})`}
                  {f === "completed" && ` (${stats.completed})`}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Task creation form */}
        {showAddForm && (
          <div className="mb-8 animate-in slide-in-from-top duration-200">
            <TaskForm
              onSubmit={handleTaskCreated}
              onCancel={() => setShowAddForm(false)}
            />
          </div>
        )}

        {/* Task list */}
        <TaskList
          tasks={filteredTasks}
          isLoading={isLoading}
          onToggle={toggleTask}
          onEdit={handleEdit}
          onDelete={handleDelete}
          emptyMessage={
            filter === "all"
              ? undefined
              : filter === "active"
                ? "No active tasks! Take a break or add a new task."
                : "No completed tasks yet. Keep going!"
          }
          onAddTask={() => setShowAddForm(true)}
        />

        {/* Edit dialog */}
        {editingTask && (
          <TaskEditDialog
            task={editingTask}
            onSave={async (data) => {
              await updateTask(editingTask.id, data);
              setEditingTask(null);
            }}
            onCancel={() => setEditingTask(null)}
          />
        )}

        {/* Delete confirmation dialog */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
            <div className="bg-white rounded-xl p-6 max-w-sm w-full shadow-2xl animate-in zoom-in-95 duration-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex-shrink-0 w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                  <svg className="h-5 w-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Delete Task?
                </h3>
              </div>
              <p className="text-gray-600 mb-6">
                This action cannot be undone. The task will be permanently removed.
              </p>
              <div className="flex justify-end gap-3">
                <Button
                  variant="secondary"
                  onClick={() => setShowDeleteConfirm(null)}
                >
                  Cancel
                </Button>
                <Button
                  variant="danger"
                  onClick={confirmDelete}
                >
                  Delete
                </Button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Mobile Add Button (Fixed) */}
      {!showAddForm && (
        <button
          onClick={() => setShowAddForm(true)}
          className="sm:hidden fixed bottom-6 right-6 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 hover:shadow-xl transition-all flex items-center justify-center z-40"
          aria-label="Add new task"
        >
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
      )}
    </div>
  );
}
