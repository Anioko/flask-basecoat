import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function CourseDetails() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-2xl font-bold text-balance">
          The Ultimate Guide to Usability Testing and UX Law
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground leading-relaxed">
          In this comprehensive course, we&#39;ll delve into the fundamentals of usability testing
          and explore the critical principles of UX law. Whether you&#39;re a seasoned UX
          professional or just starting your journey, this course is designed to equip you with the
          essential skills and knowledge needed to excel in the field.
        </p>

        <div className="space-y-4">
          <div>
            <h3 className="mb-2 font-semibold">Usability Testing:</h3>
            <p className="text-muted-foreground leading-relaxed">
              Discover how to plan, conduct, and analyze usability tests to uncover insights about
              user behavior and preferences. Learn various testing methods, tools, and techniques,
              and gain practical experience through hands-on exercises and real-world case studies.
            </p>
          </div>

          <div>
            <h3 className="mb-2 font-semibold">UX Law:</h3>
            <p className="text-muted-foreground leading-relaxed">
              Dive into the legal aspects of user experience design, including privacy regulations,
              accessibility standards, and copyright laws. Understand how to navigate legal
              frameworks and ensure compliance with industry regulations to create ethical and
              inclusive digital experiences.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
