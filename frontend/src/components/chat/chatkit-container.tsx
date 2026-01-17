"use client";

import { ChatKit, useChatKit } from "@openai/chatkit-react";
import { useState } from "react";

/**
 * ChatKit container using OpenAI's hosted chat UI.
 */
export function ChatKitContainer() {
  const [error, setError] = useState<string | null>(null);

  const { control } = useChatKit({
    api: {
      async getClientSecret(currentSecret) {
        const res = await fetch("/api/chatkit/session", {
          method: "POST",
          credentials: "include",
        });
        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.error || "Failed to get session");
        }
        const data = await res.json();
        return data.client_secret;
      },
    },
    theme: "light",
    startScreen: {
      greeting: "How can I help with your tasks?",
      prompts: [
        { label: "Show my tasks", prompt: "List all my tasks" },
        { label: "Add a task", prompt: "Add a new task: " },
      ],
    },
    onError: (e) => setError(e.error?.message || "ChatKit error"),
  });

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center p-4 max-w-md">
          <p className="text-red-600 mb-4">{error}</p>
          {error.includes("WORKFLOW_ID") && (
            <div className="text-sm text-gray-600 text-left">
              <p className="mb-2">To set up ChatKit:</p>
              <ol className="list-decimal list-inside space-y-1">
                <li>Go to <a href="https://platform.openai.com/agents" target="_blank" className="text-blue-600 hover:underline">platform.openai.com/agents</a></li>
                <li>Create a new workflow/agent</li>
                <li>Copy the workflow ID</li>
                <li>Add to .env.local: <code className="bg-gray-200 px-1">OPENAI_CHATKIT_WORKFLOW_ID=your-id</code></li>
                <li>Restart the frontend</li>
              </ol>
            </div>
          )}
          <button
            onClick={() => window.location.reload()}
            className="mt-4 text-blue-600 hover:underline"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      <ChatKit control={control} style={{ height: "100%", width: "100%" }} />
    </div>
  );
}
