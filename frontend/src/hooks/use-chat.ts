"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import {
  sendChatMessage,
  getConversationHistory,
  type ChatEvent,
  type Message,
} from "@/lib/chat-api";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "tool";
  content: string;
  isStreaming?: boolean;
  toolInfo?: {
    tool: string;
    status: string;
    result?: string;
  };
}

interface UseChatReturn {
  messages: ChatMessage[];
  sendMessage: (content: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
  conversationId: string | null;
}

/**
 * React hook for managing chat state and interactions.
 *
 * Per spec SC-004: Conversation history preserved and accessible.
 * Per spec FR-013: Tool execution metadata included in responses.
 */
export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const messageIdCounter = useRef(0);

  // Generate unique message IDs
  const generateId = useCallback(() => {
    messageIdCounter.current += 1;
    return `msg-${Date.now()}-${messageIdCounter.current}`;
  }, []);

  // Load conversation history on mount
  useEffect(() => {
    if (isInitialized) return;

    const loadHistory = async () => {
      try {
        const history = await getConversationHistory();
        if (history.conversation_id) {
          setConversationId(history.conversation_id);
        }

        // Convert history to chat messages
        const chatMessages: ChatMessage[] = history.messages.map((msg) => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
        }));

        setMessages(chatMessages);
      } catch (err) {
        console.error("Failed to load conversation history:", err);
        // Don't set error - just start fresh
      } finally {
        setIsInitialized(true);
      }
    };

    loadHistory();
  }, [isInitialized]);

  // Send a message and handle streaming response
  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading) return;

      setIsLoading(true);
      setError(null);

      // Add user message immediately
      const userMessageId = generateId();
      const userMessage: ChatMessage = {
        id: userMessageId,
        role: "user",
        content: content.trim(),
      };

      setMessages((prev) => [...prev, userMessage]);

      // Create placeholder for assistant response
      const assistantMessageId = generateId();
      let assistantContent = "";

      setMessages((prev) => [
        ...prev,
        {
          id: assistantMessageId,
          role: "assistant",
          content: "",
          isStreaming: true,
        },
      ]);

      try {
        for await (const event of sendChatMessage(content)) {
          switch (event.type) {
            case "thinking":
              // Update assistant message with thinking indicator
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: event.content || "Thinking..." }
                    : msg
                )
              );
              break;

            case "tool_call":
              // Add tool call info
              if (event.tool) {
                const toolMessage: ChatMessage = {
                  id: generateId(),
                  role: "tool",
                  content: `Calling ${event.tool}...`,
                  toolInfo: {
                    tool: event.tool,
                    status: "executing",
                  },
                };
                setMessages((prev) => {
                  // Insert before the assistant message placeholder
                  const assistantIdx = prev.findIndex(
                    (m) => m.id === assistantMessageId
                  );
                  if (assistantIdx >= 0) {
                    return [
                      ...prev.slice(0, assistantIdx),
                      toolMessage,
                      ...prev.slice(assistantIdx),
                    ];
                  }
                  return [...prev, toolMessage];
                });
              }
              break;

            case "tool_result":
              // Update the tool message with result
              if (event.tool) {
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.role === "tool" &&
                    msg.toolInfo?.tool === event.tool &&
                    msg.toolInfo?.status === "executing"
                      ? {
                          ...msg,
                          content: event.result || "",
                          toolInfo: {
                            tool: event.tool!,
                            status: event.status || "completed",
                            result: event.result,
                          },
                        }
                      : msg
                  )
                );
              }
              break;

            case "response":
              // Update assistant message with final response
              assistantContent = event.content || "";
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: assistantContent, isStreaming: false }
                    : msg
                )
              );
              break;

            case "done":
              if (event.conversation_id) {
                setConversationId(event.conversation_id);
              }
              // Mark streaming as complete
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, isStreaming: false }
                    : msg
                )
              );
              break;

            case "error":
              setError(event.content || "An error occurred");
              // Remove placeholder if no content
              if (!assistantContent) {
                setMessages((prev) =>
                  prev.filter((msg) => msg.id !== assistantMessageId)
                );
              }
              break;
          }
        }
      } catch (err) {
        console.error("Chat error:", err);
        setError(err instanceof Error ? err.message : "Failed to send message");
        // Remove placeholder
        setMessages((prev) =>
          prev.filter((msg) => msg.id !== assistantMessageId)
        );
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading, generateId]
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    messages,
    sendMessage,
    isLoading,
    error,
    clearError,
    conversationId,
  };
}
