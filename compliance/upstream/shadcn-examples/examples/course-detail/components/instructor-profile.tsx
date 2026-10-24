import { Star } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export function InstructorProfile() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Instructor</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex gap-4">
          <Avatar className="h-16 w-16">
            <AvatarImage src="/professional-instructor-headshot.jpg" />
            <AvatarFallback>DT</AvatarFallback>
          </Avatar>

          <div className="flex-1 space-y-2">
            <div>
              <h3 className="text-lg font-semibold">David Travis</h3>
              <div className="flex items-center gap-1">
                {[...Array(4)].map((_, i) => (
                  <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                ))}
                <Star className="h-4 w-4 fill-yellow-400/50 text-yellow-400" />
                <span className="text-muted-foreground ml-2 text-sm">4.5 rating</span>
              </div>
            </div>

            <p className="text-muted-foreground text-sm leading-relaxed">
              I'm on a mission to create more user experience professionals. Perhaps you'd like a
              job in user experience. Or maybe you already work in the field but you've never had
              any formal training.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
