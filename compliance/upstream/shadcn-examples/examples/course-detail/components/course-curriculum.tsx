import { Play, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const lessons = [
  { id: 1, title: "Introduction to Usability Testing", duration: "0:23", isActive: true },
  { id: 2, title: "Usability Tests: Goals and More", duration: "0:11", isActive: false },
  { id: 3, title: "Creating Usability Testing Scenarios", duration: "7:32", isActive: false },
  { id: 4, title: "Analyzing Usability Test Results", duration: "6:34", isActive: false },
  { id: 5, title: "Iterative Design and Usability Testing", duration: "2:56", isActive: false },
  { id: 6, title: "Introduction to UX Law", duration: "1:23", isActive: false },
  { id: 7, title: "Privacy Laws and User Data Protection", duration: "2:34", isActive: false },
  { id: 8, title: "Accessibility Standards and Guidelines", duration: "8:21", isActive: false },
  { id: 9, title: "Usability Testing and Legal Compliance", duration: "2:11", isActive: false },
  { id: 10, title: "Designing Ethical User Experiences", duration: "3:42", isActive: false },
  { id: 11, title: "Managing Legal Risks in UX Design", duration: "1:34", isActive: false },
  { id: 12, title: "Creating a UX Law Compliance Plan", duration: "2:01", isActive: false }
];

export function CourseCurriculum() {
  return (
    <div className="space-y-6">
      {/* Course Actions */}
      <Card>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary">Advanced</Badge>
            <Badge variant="outline">Live Class</Badge>
            <Badge variant="outline">24 Classes</Badge>
          </div>

          <div className="space-y-3">
            <Button className="w-full" size="lg">
              <Play />
              Enroll Now
            </Button>
            <Button variant="outline" className="w-full bg-transparent">
              Add to Favorites
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Course Curriculum */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Play className="text-primary h-5 w-5" />
            Course Curriculum
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="space-y-1">
            {lessons.map((lesson) => (
              <button
                key={lesson.id}
                className={`hover:bg-muted/50 w-full border-l-2 p-4 text-left transition-colors ${
                  lesson.isActive ? "border-l-primary bg-primary/5" : "border-l-transparent"
                }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className={`flex h-8 w-8 items-center justify-center rounded-full ${
                        lesson.isActive ? "bg-primary text-primary-foreground" : "bg-muted"
                      }`}>
                      <Play className="h-3 w-3" />
                    </div>
                    <div>
                      <p
                        className={`text-sm font-medium text-pretty ${
                          lesson.isActive ? "text-primary" : "text-foreground"
                        }`}>
                        {lesson.title}
                      </p>
                    </div>
                  </div>
                  <div className="text-muted-foreground flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    <span className="text-xs">{lesson.duration}</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
