import { Suspense } from "react";
import dynamic from "next/dynamic";
import Effects from "@/app/demo/[slug]/effects";
import { LoaderIcon } from "lucide-react";
import * as React from "react";

export default function DemoPageGenerator({ name }: { name: string }) {
  const Component = dynamic(() => import(`@/examples/${name}/page.tsx`), {
    ssr: true
  });

  return (
    <Suspense
      fallback={
        <div className="flex h-[500px] items-center justify-center">
          <LoaderIcon className="text-muted-foreground animate-spin lg:size-8" />
        </div>
      }>
      <Effects />
      <div className="bg-background">
        <Component />
      </div>
    </Suspense>
  );
}
