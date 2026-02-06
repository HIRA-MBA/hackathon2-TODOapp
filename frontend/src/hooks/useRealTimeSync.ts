"use client";

/**
 * Real-Time Task Synchronization Hook.
 *
 * Per T043: Provides real-time task updates via WebSocket connection.
 * Integrates with useTasks to automatically update task list when
 * changes occur on other devices/tabs.
 */

import { useEffect, useState, useCallback, useRef } from "react";
import {
  WebSocketManager,
  getWebSocketManager,
  disconnectWebSocket,
  ConnectionStatus,
  TaskUpdatePayload,
} from "@/lib/websocket";
export type { ConnectionStatus } from "@/lib/websocket";
import type { Task } from "@/lib/types";

interface UseRealTimeSyncOptions {
  /** Authentication token for WebSocket connection */
  token: string | null;
  /** Whether to enable real-time sync (default: true) */
  enabled?: boolean;
  /** Callback when a task is created remotely */
  onTaskCreated?: (task: Task) => void;
  /** Callback when a task is updated remotely */
  onTaskUpdated?: (task: Task) => void;
  /** Callback when a task is deleted remotely */
  onTaskDeleted?: (taskId: string) => void;
}

interface UseRealTimeSyncReturn {
  /** Current connection status */
  status: ConnectionStatus;
  /** Whether connected and subscribed */
  isConnected: boolean;
  /** Manually reconnect */
  reconnect: () => void;
  /** Manually disconnect */
  disconnect: () => void;
}

/**
 * Hook for real-time task synchronization via WebSocket.
 *
 * Usage:
 * ```tsx
 * const { status, isConnected } = useRealTimeSync({
 *   token: session?.accessToken,
 *   onTaskCreated: (task) => setTasks(prev => [task, ...prev]),
 *   onTaskUpdated: (task) => setTasks(prev => prev.map(t => t.id === task.id ? task : t)),
 *   onTaskDeleted: (id) => setTasks(prev => prev.filter(t => t.id !== id)),
 * });
 * ```
 */
export function useRealTimeSync(
  options: UseRealTimeSyncOptions
): UseRealTimeSyncReturn {
  const { token, enabled = true, onTaskCreated, onTaskUpdated, onTaskDeleted } = options;

  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const wsManagerRef = useRef<WebSocketManager | null>(null);
  const callbacksRef = useRef({ onTaskCreated, onTaskUpdated, onTaskDeleted });

  // Keep callbacks ref up to date
  useEffect(() => {
    callbacksRef.current = { onTaskCreated, onTaskUpdated, onTaskDeleted };
  }, [onTaskCreated, onTaskUpdated, onTaskDeleted]);

  // Handle task updates from WebSocket
  const handleTaskUpdate = useCallback((update: TaskUpdatePayload) => {
    const { action, taskId, task } = update;
    const callbacks = callbacksRef.current;

    switch (action) {
      case "created":
        if (task && callbacks.onTaskCreated) {
          callbacks.onTaskCreated(mapTaskFromWs(task));
        }
        break;

      case "updated":
        if (task && callbacks.onTaskUpdated) {
          callbacks.onTaskUpdated(mapTaskFromWs(task));
        }
        break;

      case "deleted":
        if (callbacks.onTaskDeleted) {
          callbacks.onTaskDeleted(taskId);
        }
        break;
    }
  }, []);

  // Connect to WebSocket when token is available
  useEffect(() => {
    if (!enabled || !token) {
      return;
    }

    const wsManager = getWebSocketManager(token, {
      onStatusChange: setStatus,
      onTaskUpdate: handleTaskUpdate,
      onError: (error) => {
        console.error("WebSocket error:", error.message);
      },
    });

    wsManagerRef.current = wsManager;
    wsManager.connect();

    return () => {
      // Don't disconnect on unmount - let the manager handle reconnection
      // Only disconnect when explicitly requested or token changes
    };
  }, [token, enabled, handleTaskUpdate]);

  // Disconnect when disabled or token is removed
  useEffect(() => {
    if (!enabled || !token) {
      disconnectWebSocket();
      setStatus("disconnected");
    }
  }, [enabled, token]);

  const reconnect = useCallback(() => {
    if (wsManagerRef.current) {
      wsManagerRef.current.connect();
    }
  }, []);

  const disconnect = useCallback(() => {
    disconnectWebSocket();
    wsManagerRef.current = null;
    setStatus("disconnected");
  }, []);

  return {
    status,
    isConnected: status === "connected",
    reconnect,
    disconnect,
  };
}

/**
 * Map WebSocket task payload to frontend Task type.
 */
function mapTaskFromWs(wsTask: TaskUpdatePayload["task"]): Task {
  if (!wsTask) {
    throw new Error("Cannot map null task");
  }

  return {
    id: wsTask.id,
    title: wsTask.title,
    description: wsTask.description,
    completed: wsTask.completed,
    priority: wsTask.priority as Task["priority"],
    dueDate: wsTask.dueDate,
    createdAt: wsTask.createdAt,
    updatedAt: wsTask.updatedAt,
  };
}

/**
 * Connection status indicator component props.
 */
export interface ConnectionStatusProps {
  status: ConnectionStatus;
  className?: string;
}

/**
 * Get status color for indicator.
 */
export function getStatusColor(status: ConnectionStatus): string {
  switch (status) {
    case "connected":
      return "bg-green-500";
    case "connecting":
      return "bg-yellow-500 animate-pulse";
    case "disconnected":
      return "bg-gray-400";
    case "error":
      return "bg-red-500";
    default:
      return "bg-gray-400";
  }
}

/**
 * Get status text for display.
 */
export function getStatusText(status: ConnectionStatus): string {
  switch (status) {
    case "connected":
      return "Live";
    case "connecting":
      return "Connecting...";
    case "disconnected":
      return "Offline";
    case "error":
      return "Connection error";
    default:
      return "Unknown";
  }
}
