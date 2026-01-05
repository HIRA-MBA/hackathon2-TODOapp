import { Navbar } from "@/components/navbar";
import { ChatContainer } from "@/components/chat/chat-container";

export const metadata = {
  title: "Chat - Todo App",
  description: "Chat with AI to manage your tasks",
};

/**
 * Chat page with AI-powered task management.
 * Per spec US1-US5: Natural language task operations.
 */
export default function ChatPage() {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 to-blue-50">
      <Navbar />

      {/* Chat area - takes remaining height */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <ChatContainer />
      </main>
    </div>
  );
}
