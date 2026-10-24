import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Example } from "@/types/example";
import { Badge } from "@/components/ui/badge";

export default function ExamplePagination({
  prevExample,
  nextExample
}: {
  prevExample: Example;
  nextExample: Example;
}) {
  return (
    <div className="grid w-full gap-4 md:flex-row lg:mt-20 lg:grid-cols-2">
      {prevExample ? (
        <Link href={prevExample.href} className="min-w-0 flex-1">
          <Card className="hover:bg-muted/50 py-0 shadow-none">
            <CardContent className="flex h-full flex-col justify-between p-4">
              <div className="text-foreground flex items-center gap-2 font-medium">
                <ChevronLeft className="h-4 w-4" />
                {prevExample.meta.title}
                {prevExample.isComing ? (
                  <Badge variant="outline" className="text-orange-500">
                    Soon
                  </Badge>
                ) : null}
                {prevExample.isNew ? (
                  <Badge variant="outline" className="text-green-600">
                    New
                  </Badge>
                ) : null}
              </div>
              <p className="text-muted-foreground mt-1 text-sm">{prevExample.info.description}</p>
            </CardContent>
          </Card>
        </Link>
      ) : (
        <div></div>
      )}

      {nextExample ? (
        <Link href={nextExample.href} className="min-w-0 flex-1">
          <Card className="hover:bg-muted/50 py-0 shadow-none">
            <CardContent className="flex h-full flex-col justify-between p-4 text-right">
              <div className="text-foreground flex items-center justify-end gap-2 font-medium">
                {nextExample.isComing ? (
                  <Badge variant="outline" className="text-orange-500">
                    Soon
                  </Badge>
                ) : null}
                {nextExample.isNew ? (
                  <Badge variant="outline" className="text-green-600">
                    New
                  </Badge>
                ) : null}
                {nextExample.meta.title}
                <ChevronRight className="h-4 w-4" />
              </div>
              <p className="text-muted-foreground mt-1 text-sm">{nextExample.info.description}</p>
            </CardContent>
          </Card>
        </Link>
      ) : (
        <div></div>
      )}
    </div>
  );
}
