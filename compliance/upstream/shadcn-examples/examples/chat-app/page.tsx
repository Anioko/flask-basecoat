import { ChatMain } from "./components/chat-main";
import { ChatSidebar } from "./components/chat-sidebar";

export default function Home() {
  return (
    <div className="flex h-screen">
      <ChatSidebar />
      <ChatMain />
    </div>
  );
}
