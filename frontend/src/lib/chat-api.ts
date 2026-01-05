/**
 * Chat API client with SSE streaming support.
 * Per spec FR-001: Single chat endpoint for natural language messages.
 */

export interface ChatEvent {
  type: "thinking" | "tool_call" | "tool_result" | "response" | "done" | "error";
  content?: string;
  tool?: string;
  status?: string;
  result?: string;
  conversation_id?: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "tool";
  content: string;
  created_at: string;
}

export interface ConversationHistory {
  conversation_id: string;
  messages: Message[];
}

/**
 * Send a chat message and receive streaming events.
 *
 * @param message - The user's message
 * @yields ChatEvent objects as they arrive from the server
 */
export async function* sendChatMessage(
  message: string
): AsyncGenerator<ChatEvent, void, unknown> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    if (response.status === 401) {
      window.location.href = "/signin?error=session_expired";
      return;
    }
    throw new Error(`Chat request failed: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("Response body is not readable");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });

      // Parse SSE events from buffer
      const lines = buffer.split("\n");
      buffer = lines.pop() || ""; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith("data:")) {
          const data = line.slice(5).trim();
          if (data) {
            try {
              const event = JSON.parse(data) as ChatEvent;
              yield event;

              // Stop if we received done or error
              if (event.type === "done" || event.type === "error") {
                return;
              }
            } catch {
              console.warn("Failed to parse SSE event:", data);
            }
          }
        }
      }
    }

    // Process any remaining data in buffer
    if (buffer.startsWith("data:")) {
      const data = buffer.slice(5).trim();
      if (data) {
        try {
          yield JSON.parse(data) as ChatEvent;
        } catch {
          console.warn("Failed to parse final SSE event:", data);
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * Get the user's conversation history.
 *
 * @param limit - Maximum number of messages to retrieve
 * @returns Conversation history with messages
 */
export async function getConversationHistory(
  limit: number = 50
): Promise<ConversationHistory> {
  const response = await fetch(`/api/chat/history?limit=${limit}`, {
    credentials: "include",
  });

  if (!response.ok) {
    if (response.status === 401) {
      window.location.href = "/signin?error=session_expired";
      throw new Error("Session expired");
    }
    throw new Error(`Failed to fetch history: ${response.statusText}`);
  }

  return response.json();
}
