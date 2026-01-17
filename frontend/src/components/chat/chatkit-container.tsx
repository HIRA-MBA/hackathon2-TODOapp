"use client";

import { ChatKit, useChatKit } from "@openai/chatkit-react";
import { useState, useEffect } from "react";

/**
 * ChatKit container using OpenAI's hosted chat UI.
 */
export function ChatKitContainer() {
  const [error, setError] = useState<string | null>(null);
  const [debug, setDebug] = useState<string>("");
  const [hostname, setHostname] = useState<string>("");

  const domainKey = process.env.NEXT_PUBLIC_OPENAI_DOMAIN_KEY;

  useEffect(() => {
    // Debug: log domain key status and current domain
    const host = window.location.hostname;
    setHostname(host);
    console.log("ChatKit domainKey:", domainKey ? `${domainKey.substring(0, 20)}...` : "NOT SET");
    console.log("ChatKit current domain:", host);
    console.log("ChatKit component mounted");
    if (!domainKey) {
      setDebug("NEXT_PUBLIC_OPENAI_DOMAIN_KEY is not set");
    }
  }, [domainKey]);

  const { control } = useChatKit({
    api: {
      async getClientSecret(currentSecret) {
        console.log("ChatKit: Fetching client secret...");
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

  // Show debug info if domain key is missing
  if (!domainKey) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center p-4 max-w-md">
          <p className="text-red-600 mb-4">Domain key not configured</p>
          <p className="text-sm text-gray-600">
            Set <code className="bg-gray-200 px-1">NEXT_PUBLIC_OPENAI_DOMAIN_KEY</code> in your environment variables.
          </p>
          <p className="text-xs text-gray-500 mt-2">
            For Vercel: Add it in Project Settings → Environment Variables, then redeploy.
          </p>
        </div>
      </div>
    );
  }

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
      <div className="bg-blue-50 border-b border-blue-200 px-4 py-1 text-xs text-blue-700">
        ChatKit loaded | Domain: {hostname} | Key: {domainKey?.substring(0, 15)}...
      </div>
      {debug && (
        <div className="bg-yellow-50 border-b border-yellow-200 px-4 py-2 text-sm text-yellow-800">
          Debug: {debug}
        </div>
      )}
      <ChatKit control={control} domainKey={domainKey} style={{ height: "100%", width: "100%" }} />
    </div>
  );
}
