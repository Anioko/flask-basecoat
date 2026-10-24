import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  FolderUpIcon,
  SquareKanbanIcon,
  PanelTopIcon,
  BookOpenTextIcon,
  CircleDollarSignIcon,
  ClipboardCheckIcon,
  ImageUpIcon,
  MailIcon,
  ListTodoIcon,
  CookieIcon,
  PartyPopperIcon,
  ExternalLinkIcon
} from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { routes } from "@/lib/routes";

const updates = [
  {
    date: "2025-07-02",
    type: "Feature",
    title: "Empty States Pages",
    description: "Added clean empty state layouts with clear call-to-actions.",
    icon: <PanelTopIcon className="h-5 w-5" />,
    color: "bg-teal-500",
    url: "#"
  },
  {
    date: "2025-06-28",
    type: "Feature",
    title: "Onboarding Flow Screens",
    description: "New onboarding screens to guide users step by step.",
    icon: <BookOpenTextIcon className="h-5 w-5" />,
    color: "bg-green-500",
    url: "#"
  },
  {
    date: "2025-06-28",
    type: "Feature",
    title: "Finance Dashboard",
    description: "Track revenue, expenses, and insights in a new dashboard.",
    icon: <CircleDollarSignIcon className="h-5 w-5" />,
    color: "bg-lime-600",
    url: "#"
  },
  {
    date: "2025-06-22",
    type: "Feature",
    title: "Tasks App",
    description: "Manage tasks with deadlines, priorities, and progress tracking.",
    icon: <ClipboardCheckIcon className="h-5 w-5" />,
    color: "bg-orange-500",
    url: "#"
  },
  {
    date: "2025-06-13",
    type: "Feature",
    title: "AI Image Generator",
    description: "Generate images with AI using prompts and style options.",
    icon: <ImageUpIcon className="h-5 w-5" />,
    color: "bg-blue-500",
    url: "#"
  },
  {
    date: "2025-06-13",
    type: "Feature",
    title: "Mail App",
    description: "Responsive mail client with inbox, search, and composer.",
    icon: <MailIcon className="h-5 w-5" />,
    color: "bg-purple-500",
    url: "#"
  },
  {
    date: "2025-06-12",
    type: "Feature",
    title: "Todo List App",
    description: "Simple to-do app with categories and quick add support.",
    icon: <ListTodoIcon className="h-5 w-5" />,
    color: "bg-orange-500",
    url: "#"
  },
  {
    date: "2025-05-18",
    type: "Feature",
    title: "POS App",
    description: "Point-of-sale app with catalog, orders, and sales tracking.",
    icon: <CookieIcon className="h-5 w-5" />,
    color: "bg-yellow-600",
    url: "#"
  },
  {
    date: "2024-09-24",
    type: "Major Release",
    title: "MyApp First Launch",
    description:
      "First release with over 50 components, website templates and dashboard templates.",
    icon: <PartyPopperIcon className="h-5 w-5" />,
    color: "bg-gradient-to-r from-blue-600 to-purple-600",
    url: "#"
  }
];

export type UpdatesType = (typeof updates)[number];

const Updates = () => {
  const getTypeColor = (type: string) => {
    switch (type) {
      case "Feature":
        return "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300";
      case "Enhancement":
        return "bg-blue-100 text-blue-700";
      case "Bug Fix":
        return "bg-red-100 text-red-700";
      case "Major Release":
        return "bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric"
    });
  };

  return (
    <div className="py-10 lg:py-14">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        <header className="mb-8 max-w-(--breakpoint-sm) lg:mb-12">
          <h1 className="mb-4 text-2xl font-semibold sm:text-3xl">Updates</h1>
          <p className="text-muted-foreground">
            We’re sharing the latest features and major updates to the MyApp on this page. Stay
            tuned for what’s new!
          </p>
          <Badge variant="outline" className="mt-4">
            Last update:{" "}
            <span className="text-muted-foreground">{formatDate(updates.slice(0)[0].date)}</span>
          </Badge>
        </header>

        <div className="space-y-4">
          {updates.map((update: UpdatesType, i) => (
            <Card key={i} className="gap-3 shadow-none">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex gap-4">
                    <div
                      className={`mt-1 size-10 ${update.color} flex items-center justify-center rounded-lg text-white`}>
                      {update.icon}
                    </div>
                    <div>
                      <CardTitle className="mb-1 text-lg font-semibold">{update.title}</CardTitle>
                      <div className="flex items-center gap-3">
                        <Badge variant="secondary" className={getTypeColor(update.type)}>
                          {update.type}
                        </Badge>
                        <span className="text-muted-foreground text-sm">
                          {formatDate(update.date)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                {update.url && (
                  <CardAction>
                    <Button variant="secondary" asChild>
                      <Link title="Live preview" href={`${update.url}`} target="_blank">
                        <ExternalLinkIcon />
                      </Link>
                    </Button>
                  </CardAction>
                )}
              </CardHeader>
              <CardContent className="pt-0">
                <p className="text-muted-foreground text-sm leading-relaxed">
                  {update.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="bg-muted mt-10 rounded-lg p-8 text-center">
          <h3 className="mb-4 text-xl font-semibold">Have suggestions for new features?</h3>
          <div className="flex flex-col justify-center gap-4 sm:flex-row">
            <Button asChild>
              <Link href="#">Contact Us</Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Updates;
