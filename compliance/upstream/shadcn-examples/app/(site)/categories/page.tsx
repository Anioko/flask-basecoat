import data from "@/app/(site)/[slug]/data.json";
import { Metadata } from "next";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";

export const metadata: Metadata = {
  title: "Categories - Shadcn UI Examples",
  description: "..."
};

export default function Page() {
  return (
    <div className="container mx-auto space-y-10 px-4 py-10 lg:space-y-20 lg:py-20">
      <header className="mx-auto max-w-4xl space-y-4 text-center">
        <h1 className="text-3xl font-semibold lg:text-5xl lg:leading-14">
          Advanced Shadcn UI Templates & Example Apps
        </h1>
        <p className="text-muted-foreground mx-auto max-w-2xl lg:text-lg">
          Discover a collection of applications and components built with Shadcn UI optimized for
          React and Tailwind CSS. Open source and easy to use: download or integrate directly into
          your project via the registry. Includes {data.length} ready-made example applications.
        </p>
      </header>

      <div className="mb-6 grid grid-cols-5 gap-4">
        {data.map((item, i) => (
          <Button
            key={i}
            variant="outline"
            className="relative rounded-lg lg:h-16"
            asChild={!item?.isComing}
            disabled={!!item?.isComing}>
            <Link href={`/${item.href}`}>
              {item.meta.title}
              {item?.isComing ? "(Soon)" : false}
              {item?.isNew ? (
                <Badge className="absolute -end-2 -top-2 bg-green-600">New</Badge>
              ) : (
                false
              )}
            </Link>
          </Button>
        ))}
      </div>
    </div>
  );
}
