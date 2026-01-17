"use client";

type ChatMode = "custom" | "chatkit";

interface ChatModeToggleProps {
  mode: ChatMode;
  onModeChange: (mode: ChatMode) => void;
}

/**
 * Toggle between Custom chat (openai-agents) and ChatKit.
 */
export function ChatModeToggle({ mode, onModeChange }: ChatModeToggleProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-500 font-medium">Mode:</span>
      <div className="flex rounded-md overflow-hidden border border-gray-200">
        <button
          onClick={() => onModeChange("custom")}
          className={`px-3 py-1 text-xs font-medium transition-colors ${
            mode === "custom"
              ? "bg-blue-600 text-white"
              : "bg-white text-gray-600 hover:bg-gray-100"
          }`}
        >
          Custom
        </button>
        <button
          onClick={() => onModeChange("chatkit")}
          className={`px-3 py-1 text-xs font-medium transition-colors ${
            mode === "chatkit"
              ? "bg-blue-600 text-white"
              : "bg-white text-gray-600 hover:bg-gray-100"
          }`}
        >
          ChatKit
        </button>
      </div>
    </div>
  );
}
