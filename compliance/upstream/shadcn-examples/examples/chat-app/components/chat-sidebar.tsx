"use client";

import { useState } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Search, User, Users } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatContactProps {
  id: string;
  name: string;
  avatarSrc: string;
  lastMessage: string;
  timestamp: string;
  hasUnread: boolean;
  isActive: boolean;
  onClick: (id: string) => void;
}

const ChatContact = ({
  id,
  name,
  avatarSrc,
  lastMessage,
  timestamp,
  hasUnread,
  isActive,
  onClick
}: ChatContactProps) => (
  <div
    className={cn(
      "hover:bg-muted flex cursor-pointer items-center gap-3 rounded-lg p-3 transition-colors",
      isActive && "bg-muted"
    )}
    onClick={() => onClick(id)}>
    <Avatar>
      <AvatarImage src={avatarSrc} alt={name} />
      <AvatarFallback>{name.charAt(0)}</AvatarFallback>
    </Avatar>
    <div className="flex-1">
      <div className="flex items-center justify-between">
        <span className="font-medium">{name}</span>
        <span className="text-muted-foreground text-xs">{timestamp}</span>
      </div>
      <div className="text-muted-foreground flex items-center justify-between text-sm">
        <p className="truncate">{lastMessage}</p>
        {hasUnread && <div className="ml-2 h-2 w-2 rounded-full bg-blue-500" />}
      </div>
    </div>
  </div>
);

export function ChatSidebar() {
  const [activeTab, setActiveTab] = useState("personal");
  const [activeChatId, setActiveChatId] = useState("1"); // Default active chat

  const chatContacts = [
    {
      id: "1",
      name: "Shannon Baker",
      avatarSrc: "/placeholder.svg?height=40&width=40",
      lastMessage: "Will do. Appreciat...",
      timestamp: "07:39 AM",
      hasUnread: false
    },
    {
      id: "2",
      name: "Jessica Wells",
      avatarSrc: "/placeholder.svg?height=40&width=40",
      lastMessage: "Perfect. I'll pack...",
      timestamp: "05:39 PM",
      hasUnread: true
    },
    {
      id: "3",
      name: "Arlene Pierce",
      avatarSrc: "/placeholder.svg?height=40&width=40",
      lastMessage: "Okay, Thanks 👋",
      timestamp: "03:49 PM",
      hasUnread: false
    },
    {
      id: "4",
      name: "Max Alexander",
      avatarSrc: "/placeholder.svg?height=40&width=40",
      lastMessage: "I'd love that! Let's ...",
      timestamp: "01:59 PM",
      hasUnread: false
    },
    {
      id: "5",
      name: "Jeremiah Minsk",
      avatarSrc: "/placeholder.svg?height=40&width=40",
      lastMessage: "No problem. G... 😬",
      timestamp: "02:59 AM",
      hasUnread: false
    },
    {
      id: "6",
      name: "Camila Simmons",
      avatarSrc: "/placeholder.svg?height=40&width=40",
      lastMessage: "True! I'll be more c...",
      timestamp: "10:19 PM",
      hasUnread: false
    }
  ];

  return (
    <div className="flex w-80 flex-col border border-r p-4">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Chat</h1>
        <Search className="text-muted-foreground h-5 w-5 cursor-pointer" />
      </div>

      <div className="mb-6 flex rounded-lg border p-1">
        <Button
          variant="ghost"
          className={cn(
            "h-9 flex-1 rounded-md text-sm font-medium",
            activeTab === "personal" ? "shadow-sm" : "text-muted-foreground hover:bg-transparent"
          )}
          onClick={() => setActiveTab("personal")}>
          <User className="mr-2 h-4 w-4" />
          Personal
        </Button>
        <Button
          variant="ghost"
          className={cn(
            "h-9 flex-1 rounded-md text-sm font-medium",
            activeTab === "groups" ? "shadow-sm" : "text-muted-foreground hover:bg-transparent"
          )}
          onClick={() => setActiveTab("groups")}>
          <Users className="mr-2 h-4 w-4" />
          Groups
        </Button>
      </div>

      <div className="flex-1 space-y-2 overflow-y-auto pr-2">
        {chatContacts.map((contact) => (
          <ChatContact
            key={contact.id}
            {...contact}
            isActive={contact.id === activeChatId}
            onClick={setActiveChatId}
          />
        ))}
      </div>

      <div className="mt-6">
        <Button className="w-full">New chat</Button>
      </div>
    </div>
  );
}
