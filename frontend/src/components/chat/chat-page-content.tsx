"use client";

import { useState } from "react";
import { ChatContainer } from "./chat-container";
import { ChatKitContainer } from "./chatkit-container";
import { ChatModeToggle } from "./chat-mode-toggle";

type ChatMode = "custom" | "chatkit";

/**
 * Chat page content with mode toggle.
 * Switches between custom openai-agents chat and ChatKit.
 */
export function ChatPageContent() {
  const [mode, setMode] = useState<ChatMode>("custom");

  return (
    <>
      {/* Toggle header */}
      <div className="flex justify-end px-4 py-2 border-b border-gray-100 bg-white/50">
        <ChatModeToggle mode={mode} onModeChange={setMode} />
      </div>

      {/* Chat content */}
      {mode === "custom" ? <ChatContainer /> : <ChatKitContainer />}
    </>
  );
}
