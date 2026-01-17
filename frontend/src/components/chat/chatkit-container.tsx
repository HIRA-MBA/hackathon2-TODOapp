"use client";

import { ChatKit, useChatKit } from "@openai/chatkit-react";
import { useState, useEffect } from "react";

/**
 * ChatKit container using OpenAI's hosted chat UI with backend authentication.
 */
export function ChatKitContainer() {
  const [error, setError] = useState<string | null>(null);
  const [debug, setDebug] = useState<string>("");
  const [hostname, setHostname] = useState<string>("");

  useEffect(() => {
    const host = window.location.hostname;
    setHostname(host);
    console.log("ChatKit component mounted");
    console.log("ChatKit current domain:", host);
  }, []);

  const { control } = useChatKit({
    api: {
      async getClientSecret(existing) {
        console.log("ChatKit: Fetching client secret...", existing ? "(refresh)" : "(initial)");
        setDebug("Fetching session...");
        try {
          const res = await fetch("/api/chatkit/session", {
            method: "POST",
            credentials: "include",
          });
          console.log("ChatKit session response:", res.status);
          if (!res.ok) {
            const data = await res.json();
            const errMsg = data.error || "Failed to get session";
            console.error("ChatKit session error:", errMsg);
            setDebug(`Session error: ${errMsg}`);
            throw new Error(errMsg);
          }
          const data = await res.json();
          console.log("ChatKit: Got client secret");
          setDebug("");
          return data.client_secret;
        } catch (err) {
          console.error("ChatKit fetch error:", err);
          setDebug(`Fetch error: ${err}`);
          throw err;
        }
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
    onError: (e) => {
      console.error("ChatKit onError:", e);
      setError(e.error?.message || "ChatKit error");
    },
  });

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center p-4 max-w-md">
          <p className="text-red-600 mb-4">{error}</p>
          {(error.includes("WORKFLOW_ID") || error.includes("session")) && (
            <div className="text-sm text-gray-600 text-left">
              <p className="mb-2">To set up ChatKit:</p>
              <ol className="list-decimal list-inside space-y-1">
                <li>Go to <a href="https://platform.openai.com/agents" target="_blank" className="text-blue-600 hover:underline">platform.openai.com/agents</a></li>
                <li>Create a new workflow/agent</li>
                <li>Copy the workflow ID</li>
                <li>Add to environment: <code className="bg-gray-200 px-1">OPENAI_CHATKIT_WORKFLOW_ID=your-id</code></li>
                <li>Ensure <code className="bg-gray-200 px-1">OPENAI_API_KEY</code> is set</li>
                <li>Restart/redeploy the app</li>
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
    <div className="flex-1 flex flex-col w-full h-full">
      <div className="bg-blue-50 border-b border-blue-200 px-4 py-1 text-xs text-blue-700 shrink-0">
        ChatKit loaded | Domain: {hostname}
      </div>
      {debug && (
        <div className="bg-yellow-50 border-b border-yellow-200 px-4 py-2 text-sm text-yellow-800 shrink-0">
          Debug: {debug}
        </div>
      )}
      <div className="flex-1 min-h-0 relative">
        <ChatKit control={control} className="absolute inset-0" />
      </div>
    </div>
  );
}
