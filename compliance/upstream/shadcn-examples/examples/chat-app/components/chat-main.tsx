import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { ArrowRight, ImageIcon, MoreVertical } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface MessageBubbleProps {
  message: string;
  isUserMessage: boolean;
  avatarSrc?: string;
}

const MessageBubble = ({ message, isUserMessage, avatarSrc }: MessageBubbleProps) => (
  <div className={cn("flex items-start gap-3", isUserMessage ? "justify-end" : "")}>
    {!isUserMessage && (
      <Avatar className="h-8 w-8">
        <AvatarImage src={avatarSrc || "/placeholder.svg"} alt="User Avatar" />
        <AvatarFallback>U</AvatarFallback>
      </Avatar>
    )}
    <div
      className={cn(
        "max-w-[70%] rounded-lg p-3",
        isUserMessage ? "bg-primary text-primary-foreground rounded-br-none" : "rounded-bl-none"
      )}>
      <p className="text-sm">{message}</p>
    </div>
  </div>
);

export function ChatMain() {
  const currentChatUser = {
    name: "Shannon Baker",
    avatarSrc: "/placeholder.svg?height=40&width=40",
    status: "last seen recently"
  };

  const messages = [
    {
      id: "m1",
      sender: "other",
      avatarSrc: "/placeholder.svg?height=32&width=32",
      content:
        "I think you should go for it. You're more than capable and it sounds like a great opportunity for growth."
    },
    {
      id: "m2",
      sender: "user",
      content:
        "It's a bigger company and a more challenging role. I'm worried it might be too much to handle."
    },
    {
      id: "m3",
      sender: "user",
      content:
        "Thanks, Mark. I needed that encouragement. I'll start working on my application tonight."
    },
    {
      id: "m4",
      sender: "other",
      avatarSrc: "/placeholder.svg?height=32&width=32",
      content: "Anytime! Let me know if you need any help with your resume or cover letter."
    },
    {
      id: "m5",
      sender: "user",
      content: "Will do. Appreciate it!"
    }
  ];

  return (
    <div className="m-4 flex flex-1 flex-col rounded-lg shadow-sm">
      <div className="flex items-center justify-between border border-b p-4">
        <div className="flex items-center gap-3">
          <Avatar className="h-10 w-10">
            <AvatarImage
              src={currentChatUser.avatarSrc || "/placeholder.svg"}
              alt={currentChatUser.name}
            />
            <AvatarFallback>{currentChatUser.name.charAt(0)}</AvatarFallback>
          </Avatar>
          <div>
            <h2 className="font-semibold">{currentChatUser.name}</h2>
            <p className="text-muted-foreground text-sm">{currentChatUser.status}</p>
          </div>
        </div>
        <MoreVertical className="text-muted-foreground h-5 w-5 cursor-pointer" />
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto p-6">
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg.content}
            isUserMessage={msg.sender === "user"}
            avatarSrc={msg.avatarSrc}
          />
        ))}
      </div>

      <div className="flex items-center gap-3 border border-t p-4">
        <ImageIcon className="text-muted-foreground h-5 w-5 cursor-pointer" />
        <Input
          placeholder="Enter a prompt here"
          className="flex-1 border-none focus-visible:ring-0 focus-visible:ring-offset-0"
        />
        <Button size="icon" className="rounded-full">
          <ArrowRight />
        </Button>
      </div>
    </div>
  );
}
