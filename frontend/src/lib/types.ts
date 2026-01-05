/**
 * Task entity from the backend API.
 * Per data-model.md and openapi.yaml
 */
export interface Task {
  id: string;
  title: string;
  description: string | null;
  completed: boolean;
  createdAt: string;
  updatedAt: string;
}

/**
 * Request body for creating a new task.
 */
export interface TaskCreate {
  title: string;
  description?: string | null;
}

/**
 * Request body for updating a task.
 */
export interface TaskUpdate {
  title?: string;
  description?: string | null;
}

/**
 * Response from list tasks endpoint.
 */
export interface TaskListResponse {
  tasks: Task[];
  count: number;
}

/**
 * User information from Better Auth session.
 */
export interface User {
  id: string;
  email: string;
  name?: string;
}

/**
 * API error response.
 */
export interface ApiError {
  error: string;
  detail?: string;
}

/**
 * Validation error response.
 */
export interface ValidationError {
  error: string;
  details: Array<{
    field: string;
    message: string;
  }>;
}
