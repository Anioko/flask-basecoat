import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Heart, MessageCircle, Send } from "lucide-react";

interface Comment {
  id: string;
  author: {
    name: string;
    avatar: string;
  };
  content: string;
  timestamp: string;
  likes: number;
}

interface CommentSectionProps {
  comments: Comment[];
  onAddComment: (content: string) => void;
}

export const CommentSection = ({ comments, onAddComment }: CommentSectionProps) => {
  const [newComment, setNewComment] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newComment.trim()) {
      onAddComment(newComment);
      setNewComment("");
    }
  };

  return (
    <section className="space-y-6">
      <div className="border-blog-border border-t pt-12">
        <h2 className="text-foreground mb-8 flex items-center gap-2 text-2xl font-bold">
          <MessageCircle className="h-6 w-6" />
          Comments ({comments.length})
        </h2>

        {/* Comment Form */}
        <form
          onSubmit={handleSubmit}
          className="bg-card border-blog-border mb-12 rounded-xl border p-6">
          <div className="space-y-4">
            <Textarea
              placeholder="Share your thoughts..."
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              className="border-blog-border focus:border-primary min-h-[100px] resize-none"
            />
            <div className="flex justify-end">
              <Button type="submit" className="gap-2">
                <Send className="h-4 w-4" />
                Post Comment
              </Button>
            </div>
          </div>
        </form>

        {/* Comments List */}
        <div className="space-y-6">
          {comments.map((comment) => (
            <div
              key={comment.id}
              className="bg-card border-blog-border hover:bg-blog-hover rounded-xl border p-6 transition-colors">
              <div className="flex items-start space-x-4">
                <Avatar className="h-10 w-10">
                  <AvatarImage src={comment.author.avatar} alt={comment.author.name} />
                  <AvatarFallback>{comment.author.name.charAt(0)}</AvatarFallback>
                </Avatar>

                <div className="flex-1 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-foreground font-medium">{comment.author.name}</p>
                      <p className="text-blog-meta text-sm">{comment.timestamp}</p>
                    </div>
                  </div>

                  <p className="text-blog-content leading-relaxed">{comment.content}</p>

                  <div className="flex items-center gap-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-blog-meta hover:text-primary gap-2">
                      <Heart className="h-4 w-4" />
                      {comment.likes}
                    </Button>
                    <Button variant="ghost" size="sm" className="text-blog-meta hover:text-primary">
                      Reply
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
