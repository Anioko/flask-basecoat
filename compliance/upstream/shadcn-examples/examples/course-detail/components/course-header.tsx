import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export function CourseHeader() {
  return (
    <header className="bg-card/50 sticky top-0 z-50 border-b backdrop-blur-sm">
      <div className="px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="outline" size="sm" className="gap-2">
              <ArrowLeft className="h-4 w-4" />
              Courses
            </Button>
            <div className="bg-border h-6 w-px" />
            <h1 className="text-lg font-medium">
              The Ultimate Guide to Usability Testing and UX Law
            </h1>
          </div>

          <nav className="hidden items-center gap-2 md:flex">
            <Button variant="ghost" size="sm">
              All Videos
            </Button>
            <Button variant="ghost" size="sm">
              Resources
            </Button>
            <Button variant="ghost" size="sm">
              Support
            </Button>
          </nav>
        </div>
      </div>
    </header>
  );
}
