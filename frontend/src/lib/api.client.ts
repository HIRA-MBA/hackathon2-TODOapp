import type { Task, TaskCreate, TaskUpdate, TaskListResponse, ApiError } from "./types";

const API_BASE = "/api/tasks";

/**
 * API client for task operations.
 * Per ADR-002: Uses Next.js API routes as proxy to FastAPI backend.
 */
class TaskApiClient {
  private async request<T>(
    url: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      credentials: "include", // Include cookies for auth
    });

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        error: "Unknown error",
        detail: response.statusText,
      }));

      // On 401, throw an error but do NOT redirect. The middleware and
      // protected layout handle auth redirects on page navigations. Redirecting
      // here caused false "session expired" loops when the 401 was from the
      // backend proxy rather than a truly expired session.
      if (response.status === 401) {
        throw new Error("Authentication required. Please refresh the page.");
      }

      throw new Error(error.detail || error.error);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  /**
   * List all tasks for the current user.
   * @param sortBy - Sort order: "created_at" (newest first) or "due_date" (soonest first)
   */
  async listTasks(sortBy: "created_at" | "due_date" = "created_at"): Promise<TaskListResponse> {
    const url = sortBy !== "created_at" ? `${API_BASE}?sort_by=${sortBy}` : API_BASE;
    return this.request<TaskListResponse>(url);
  }

  /**
   * Get a single task by ID.
   */
  async getTask(id: string): Promise<Task> {
    return this.request<Task>(`${API_BASE}/${id}`);
  }

  /**
   * Create a new task.
   */
  async createTask(data: TaskCreate): Promise<Task> {
    return this.request<Task>(API_BASE, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  /**
   * Update a task.
   */
  async updateTask(id: string, data: TaskUpdate): Promise<Task> {
    return this.request<Task>(`${API_BASE}/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  /**
   * Toggle task completion status.
   */
  async toggleTask(id: string): Promise<Task> {
    return this.request<Task>(`${API_BASE}/${id}/toggle`, {
      method: "PATCH",
    });
  }

  /**
   * Delete a task.
   */
  async deleteTask(id: string): Promise<void> {
    return this.request<void>(`${API_BASE}/${id}`, {
      method: "DELETE",
    });
  }
}

export const taskApi = new TaskApiClient();
