import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Tag } from "lucide-react";

interface TimelineEvent {
  id: string;
  title: string;
  time: string;
  description?: string;
}

interface TimelineActivity {
  id: string;
  user: {
    name: string;
    avatar?: string;
    initials: string;
  };
  action: string;
  target?: string;
  time: string;
  status?: {
    label: string;
    variant: "default" | "secondary" | "destructive" | "outline";
  };
  comment?: string;
  tags?: Array<{
    label: string;
    variant: "default" | "secondary" | "destructive" | "outline";
  }>;
}

interface BasicTimelineProps {
  events: TimelineEvent[];
}

interface AdvancedTimelineProps {
  activities: TimelineActivity[];
}

export function BasicTimeline({ events }: BasicTimelineProps) {
  return (
    <div className="space-y-6">
      <h2 className="text-foreground text-xl font-semibold">Basic</h2>
      <div className="relative">
        {/* Timeline line */}
        <div className="bg-border absolute top-0 bottom-0 left-3 w-px" />

        <div className="space-y-8">
          {events.map((event, index) => (
            <div key={event.id} className="relative flex items-start gap-4">
              {/* Timeline dot */}
              <div className="relative z-10 flex h-6 w-6 items-center justify-center">
                <div className="bg-muted-foreground h-3 w-3 rounded-full" />
              </div>

              {/* Event content */}
              <div className="min-w-0 flex-1 pb-8">
                <div className="text-muted-foreground text-sm">
                  {event.title} - {event.time}
                </div>
                {event.description && (
                  <div className="text-foreground mt-1 text-sm">{event.description}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function AdvancedTimeline({ activities }: AdvancedTimelineProps) {
  return (
    <div className="space-y-6">
      <h2 className="text-foreground text-xl font-semibold">Advance</h2>
      <div className="relative">
        {/* Timeline line */}
        <div className="bg-border absolute top-0 bottom-0 left-6 w-px" />

        <div className="space-y-6">
          {activities.map((activity, index) => (
            <div key={activity.id} className="relative flex items-start gap-4">
              {/* Avatar */}
              <div className="relative z-10">
                <Avatar className="h-12 w-12">
                  <AvatarImage
                    src={activity.user.avatar || "/placeholder.svg"}
                    alt={activity.user.name}
                  />
                  <AvatarFallback className="bg-primary text-primary-foreground text-sm font-medium">
                    {activity.user.initials}
                  </AvatarFallback>
                </Avatar>
              </div>

              {/* Activity content */}
              <div className="min-w-0 flex-1 pb-6">
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <span className="text-foreground font-medium">{activity.user.name}</span>
                  <span className="text-muted-foreground">{activity.action}</span>
                  {activity.target && (
                    <span className="text-foreground font-medium">{activity.target}</span>
                  )}
                  {activity.status && (
                    <Badge variant={activity.status.variant} className="ml-1">
                      <div className="mr-1 h-2 w-2 rounded-full bg-green-500" />
                      {activity.status.label}
                    </Badge>
                  )}
                  <span className="text-muted-foreground ml-auto">{activity.time}</span>
                </div>

                {activity.comment && (
                  <Card className="bg-muted/50 mt-3">
                    <CardContent className="p-4">
                      <p className="text-muted-foreground text-sm leading-relaxed">
                        {activity.comment}
                      </p>
                    </CardContent>
                  </Card>
                )}

                {activity.tags && activity.tags.length > 0 && (
                  <div className="mt-3 flex items-center gap-2">
                    <Tag className="text-muted-foreground h-4 w-4" />
                    <span className="text-muted-foreground text-sm">added tags</span>
                    <div className="flex gap-2">
                      {activity.tags.map((tag, tagIndex) => (
                        <Badge key={tagIndex} variant={tag.variant} className="text-xs">
                          {tag.label}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function Page() {
  const basicEvents: TimelineEvent[] = [
    {
      id: "1",
      title: "Breakfast",
      time: "09:00"
    },
    {
      id: "2",
      title: "Lunch",
      time: "12:30"
    },
    {
      id: "3",
      title: "Dinner",
      time: "7:00"
    }
  ];

  const advancedActivities: TimelineActivity[] = [
    {
      id: "1",
      user: {
        name: "Angelina Gotelli",
        initials: "AG",
        avatar: "/professional-woman-avatar.png"
      },
      action: "has change the status to",
      status: {
        label: "Completed",
        variant: "default"
      },
      time: "6h ago"
    },
    {
      id: "2",
      user: {
        name: "Max Alexander",
        initials: "MA",
        avatar: "/professional-man-avatar.png"
      },
      action: "comment on your",
      target: "Post",
      time: "2d ago",
      comment:
        "Fine, Java MIGHT be a good example of what a programming language should be like. But Java applications are good examples of what applications SHOULDN'T be like."
    },
    {
      id: "3",
      user: {
        name: "Eugene Stewart",
        initials: "ES",
        avatar: "/developer-avatar.png"
      },
      action: "added tags",
      time: "2d ago",
      tags: [
        {
          label: "Live Issue",
          variant: "destructive"
        },
        {
          label: "Backend",
          variant: "default"
        }
      ]
    }
  ];

  return (
    <div className="mx-auto max-w-4xl space-y-12 p-6">
      <BasicTimeline events={basicEvents} />
      <AdvancedTimeline activities={advancedActivities} />
    </div>
  );
}
