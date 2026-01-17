import { Navbar } from "@/components/navbar";
import { ChatPageContent } from "@/components/chat/chat-page-content";

export const metadata = {
  title: "Chat - Todo App",
  description: "Chat with AI to manage your tasks",
};

/**
 * Chat page with AI-powered task management.
 * Supports both custom (openai-agents) and ChatKit modes.
 */
export default function ChatPage() {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 to-blue-50">
      <Navbar />

      {/* Chat area - takes remaining height */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <ChatPageContent />
      </main>
    </div>
  );
}
