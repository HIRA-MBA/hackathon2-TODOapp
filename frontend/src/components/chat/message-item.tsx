"use client";

import type { ChatMessage } from "@/hooks/use-chat";

interface MessageItemProps {
  message: ChatMessage;
}

/**
 * Individual message bubble component.
 * Handles user, assistant, and tool message types.
 */
export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === "user";
  const isTool = message.role === "tool";

  if (isTool) {
    return <ToolMessage message={message} />;
  }

  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}
    >
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-blue-500 text-white rounded-br-md"
            : "bg-gray-100 text-gray-900 rounded-bl-md"
        }`}
      >
        {/* Message content */}
        <div className="whitespace-pre-wrap break-words">
          {message.content || (
            <span className="text-gray-400 italic">
              {message.isStreaming ? (
                <span className="flex items-center gap-2">
                  <LoadingDots />
                  Thinking...
                </span>
              ) : (
                "..."
              )}
            </span>
          )}
        </div>

        {/* Streaming indicator */}
        {message.isStreaming && message.content && (
          <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse" />
        )}
      </div>
    </div>
  );
}

/**
 * Tool execution result display.
 */
function ToolMessage({ message }: { message: ChatMessage }) {
  const isSuccess = message.toolInfo?.status === "success";
  const isExecuting = message.toolInfo?.status === "executing";

  return (
    <div className="flex justify-center mb-4">
      <div
        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
          isExecuting
            ? "bg-yellow-50 text-yellow-700 border border-yellow-200"
            : isSuccess
            ? "bg-green-50 text-green-700 border border-green-200"
            : "bg-red-50 text-red-700 border border-red-200"
        }`}
      >
        {/* Icon */}
        {isExecuting ? (
          <svg
            className="w-4 h-4 animate-spin"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
        ) : isSuccess ? (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
        ) : (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        )}

        {/* Tool name and result */}
        <span className="font-medium">{message.toolInfo?.tool}</span>
        {!isExecuting && message.content && (
          <span className="text-gray-600">
            {message.content.split(" - ").slice(1).join(" - ")}
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * Animated loading dots.
 */
function LoadingDots() {
  return (
    <span className="flex gap-1">
      <span className="w-1.5 h-1.5 bg-current rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
      <span className="w-1.5 h-1.5 bg-current rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
      <span className="w-1.5 h-1.5 bg-current rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
    </span>
  );
}
