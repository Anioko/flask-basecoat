"use client";

import { useState } from "react";
import { Header } from "./components/header";
import { Content } from "./components/content";
import { CommentSection } from "./components/comment-section";
import { useRouter } from "next/navigation";

const commentsData = [
  {
    id: "1",
    author: {
      name: "Sarah Johnson",
      avatar: "/placeholder.svg"
    },
    content:
      "This is exactly what I needed! The personalization tips are incredibly valuable. I've been struggling with low open rates, and this gives me a clear direction to improve.",
    timestamp: "2 hours ago",
    likes: 12
  },
  {
    id: "2",
    author: {
      name: "Mike Chen",
      avatar: "/placeholder.svg"
    },
    content:
      "Great insights on email personalization. I especially liked the section about adding elements that spark interest. Have you tested A/B variations of these techniques?",
    timestamp: "5 hours ago",
    likes: 8
  },
  {
    id: "3",
    author: {
      name: "Emily Rodriguez",
      avatar: "/placeholder.svg"
    },
    content:
      "Thanks for sharing this comprehensive guide! The practical examples make it easy to understand how to implement these strategies in our own campaigns.",
    timestamp: "1 day ago",
    likes: 15
  }
];

const blogData = {
  category: "Company",
  title: "The Best Way to Write a Recurring Email Newsletter",
  author: {
    name: "Esther Howard",
    avatar:
      "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
  },
  publishedDate: "Nov 24, 2023",
  content: [
    "You cannot avoid the importance of the first outreach email for increasing your sales in the email campaign. But how can you move out from the crowd and evoke a meaningful and personalized response?",
    "Personalizing the emails for prospects and clients can get you the results you want from your email marketing strategy. As a result, you can engage prospects and drive them toward action, leading to a successful lead prospecting strategy in your sales outreach emails.",
    "Although you cannot personalize every email with great accuracy, you can add a few elements that are enough to spark interest.",
    "To get you in the right direction, here is the complete guide to email personalization for sales outreach that will help you create more engaging and effective email campaigns.",
    "The key to successful email marketing lies in understanding your audience deeply and crafting messages that resonate with their specific needs, challenges, and goals. This approach not only improves open rates but also builds stronger relationships with your prospects."
  ]
};

export default function Page() {
  const navigate = useRouter();

  const [comments, setComments] = useState(commentsData);

  const handleAddComment = (content: string) => {
    const newComment = {
      id: Date.now().toString(),
      author: {
        name: "You",
        avatar: "/placeholder.svg"
      },
      content,
      timestamp: "Just now",
      likes: 0
    };
    setComments([newComment, ...comments]);
  };

  return (
    <div className="bg-background min-h-screen">
      <div className="mx-auto max-w-4xl px-6 py-12">
        <Header
          category={blogData.category}
          title={blogData.title}
          author={blogData.author}
          publishedDate={blogData.publishedDate}
          onBack={() => navigate.push("/")}
        />

        <div className="mt-16">
          <Content
            content={blogData.content}
            coverImage="https://plus.unsplash.com/premium_photo-1683211783920-8c66ab120c09"
          />
        </div>

        <div className="mt-16">
          <CommentSection comments={comments} onAddComment={handleAddComment} />
        </div>
      </div>
    </div>
  );
}
