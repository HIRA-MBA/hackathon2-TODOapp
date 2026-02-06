/**
 * WebSocket Connection Manager for Real-Time Task Sync.
 *
 * Per T044: Manages WebSocket connection to the websocket-service
 * with automatic reconnection and message handling.
 */

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface TaskUpdatePayload {
  action: 'created' | 'updated' | 'deleted';
  taskId: string;
  timestamp: string;
  task: {
    id: string;
    title: string;
    description: string | null;
    completed: boolean;
    priority: string;
    dueDate: string | null;
    reminderOffset: number;
    hasRecurrence: boolean;
    parentTaskId: string | null;
    createdAt: string;
    updatedAt: string;
  } | null;
  changedFields?: string[];
}

export interface WebSocketMessage {
  type: string;
  payload?: unknown;
  timestamp?: number;
}

export interface ConnectionAckPayload {
  connectionId: string;
  userId: string;
  serverTime: string;
  reconnectToken: string;
}

export type MessageHandler = (message: WebSocketMessage) => void;
export type StatusHandler = (status: ConnectionStatus) => void;
export type TaskUpdateHandler = (update: TaskUpdatePayload) => void;

interface WebSocketManagerOptions {
  url: string;
  token: string;
  onStatusChange?: StatusHandler;
  onTaskUpdate?: TaskUpdateHandler;
  onError?: (error: Error) => void;
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
  pingInterval?: number;
}

/**
 * WebSocket connection manager with automatic reconnection.
 */
export class WebSocketManager {
  private ws: WebSocket | null = null;
  private options: Required<WebSocketManagerOptions>;
  private status: ConnectionStatus = 'disconnected';
  private reconnectAttempts = 0;
  private reconnectToken: string | null = null;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private messageHandlers: Set<MessageHandler> = new Set();

  constructor(options: WebSocketManagerOptions) {
    this.options = {
      reconnectDelay: 1000,
      maxReconnectAttempts: 10,
      pingInterval: 30000,
      onStatusChange: () => {},
      onTaskUpdate: () => {},
      onError: () => {},
      ...options,
    };
  }

  /**
   * Connect to the WebSocket server.
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.setStatus('connecting');

    // Build connection URL with token
    const url = new URL(this.options.url);
    url.searchParams.set('token', this.options.token);
    if (this.reconnectToken) {
      url.searchParams.set('reconnectToken', this.reconnectToken);
    }

    try {
      this.ws = new WebSocket(url.toString());
      this.setupEventHandlers();
    } catch (error) {
      this.setStatus('error');
      this.options.onError?.(error as Error);
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from the WebSocket server.
   */
  disconnect(): void {
    this.clearTimers();
    this.reconnectAttempts = 0;

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.setStatus('disconnected');
  }

  /**
   * Subscribe to task updates.
   */
  subscribe(scopes: string[] = ['own_tasks']): void {
    this.send({
      type: 'subscribe',
      payload: { scopes },
    });
  }

  /**
   * Unsubscribe from task updates.
   */
  unsubscribe(): void {
    this.send({ type: 'unsubscribe' });
  }

  /**
   * Send a message to the server.
   */
  send(message: WebSocketMessage): boolean {
    if (this.ws?.readyState !== WebSocket.OPEN) {
      return false;
    }

    try {
      this.ws.send(JSON.stringify(message));
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Add a message handler.
   */
  addMessageHandler(handler: MessageHandler): void {
    this.messageHandlers.add(handler);
  }

  /**
   * Remove a message handler.
   */
  removeMessageHandler(handler: MessageHandler): void {
    this.messageHandlers.delete(handler);
  }

  /**
   * Get current connection status.
   */
  getStatus(): ConnectionStatus {
    return this.status;
  }

  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      this.setStatus('connected');
      this.reconnectAttempts = 0;
      this.startPingTimer();
    };

    this.ws.onclose = (event) => {
      this.clearTimers();

      if (event.code === 4001) {
        // Auth failure - don't reconnect
        this.setStatus('error');
        this.options.onError?.(new Error('Authentication failed'));
        return;
      }

      this.setStatus('disconnected');
      this.scheduleReconnect();
    };

    this.ws.onerror = () => {
      this.setStatus('error');
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        this.handleMessage(message);
      } catch {
        console.error('Failed to parse WebSocket message');
      }
    };
  }

  private handleMessage(message: WebSocketMessage): void {
    // Notify all handlers
    this.messageHandlers.forEach((handler) => handler(message));

    switch (message.type) {
      case 'connection_ack': {
        const payload = message.payload as ConnectionAckPayload;
        this.reconnectToken = payload.reconnectToken;
        // Auto-subscribe after connection
        this.subscribe();
        break;
      }

      case 'task_update': {
        const payload = message.payload as TaskUpdatePayload;
        this.options.onTaskUpdate?.(payload);
        break;
      }

      case 'pong':
        // Heartbeat response - connection is alive
        break;

      case 'error': {
        const payload = message.payload as { code: string; message: string };
        this.options.onError?.(new Error(`${payload.code}: ${payload.message}`));
        break;
      }
    }
  }

  private setStatus(status: ConnectionStatus): void {
    if (this.status !== status) {
      this.status = status;
      this.options.onStatusChange?.(status);
    }
  }

  private startPingTimer(): void {
    this.clearTimers();
    this.pingTimer = setInterval(() => {
      this.send({
        type: 'ping',
        timestamp: Date.now(),
      });
    }, this.options.pingInterval);
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      this.setStatus('error');
      this.options.onError?.(new Error('Max reconnection attempts reached'));
      return;
    }

    const delay = this.options.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private clearTimers(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}

// Singleton instance (created per session)
let wsManager: WebSocketManager | null = null;

/**
 * Get or create the WebSocket manager instance.
 */
export function getWebSocketManager(
  token: string,
  options?: Partial<WebSocketManagerOptions>
): WebSocketManager {
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001/ws';

  if (!wsManager) {
    wsManager = new WebSocketManager({
      url: wsUrl,
      token,
      ...options,
    });
  }

  return wsManager;
}

/**
 * Disconnect and cleanup the WebSocket manager.
 */
export function disconnectWebSocket(): void {
  if (wsManager) {
    wsManager.disconnect();
    wsManager = null;
  }
}
