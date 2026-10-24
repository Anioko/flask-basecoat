import ComponentIframe from "@/app/(site)/[slug]/components/component-iframe";

import React from "react";
import Link from "next/link";
import {
  ExternalLinkIcon,
  FullscreenIcon,
  GithubIcon,
  Monitor,
  Smartphone,
  Tablet
} from "lucide-react";
import { Example } from "@/types/example";
import CodeDialog from "@/app/(site)/[slug]/components/code-dialog";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import data from "../data.json";
import ExamplePagination from "@/app/(site)/[slug]/components/pagination";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import BreakpointChanger from "@/app/(site)/[slug]/components/breakpoint-changer";

export default function ExampleDetail({ example }: { example: Example }) {
  const exampleIndex = data.findIndex((a) => a.href === example.href);
  const prevExample = data[exampleIndex - 1];
  const nextExample = data[exampleIndex + 1];

  return (
    <>
      <header className="border-b bg-linear-to-t from-transparent to-black/10 py-6 lg:py-10 dark:to-white/15">
        <div className="container mx-auto flex flex-col items-start justify-between space-y-4 px-4 lg:flex-row lg:items-center lg:space-y-0">
          <div className="space-y-3 lg:space-y-2">
            <h1 className="text-3xl font-bold lg:text-4xl">{example.meta.title}</h1>
            {example.info.description && (
              <p className="text-muted-foreground max-w-3xl text-lg">{example.info.description}</p>
            )}
          </div>
          <Button asChild>
            <Link
              href="https://github.com/shadcn-examples/shadcn-examples/discussions/categories/suggestions"
              target="_blank">
              <GithubIcon />
              Make a suggestion
            </Link>
          </Button>
        </div>
      </header>

      <div className="container mx-auto space-y-10 px-4">
        <div className="mb-4 flex space-x-3">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="outline" size="icon" asChild>
                <Link href={`/demo/${example.href}`} target="_blank">
                  <FullscreenIcon />
                </Link>
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Full Screen</p>
            </TooltipContent>
          </Tooltip>
          <BreakpointChanger id={example.href} />
          <CodeDialog example={example} />
        </div>

        <div className="block overflow-hidden rounded-lg border lg:hidden">
          <figure>
            <img
              src={`${process.env.BASE_URL}/example-images/${example.href}.png`}
              className="w-full object-cover"
              alt={`shadcn example ${example.meta.title}`}
            />
          </figure>
        </div>

        <div className="hidden lg:block">
          <ComponentIframe id={example.href} url={`/demo/${example.href}`} />
        </div>

        {example?.similars && example?.similars?.length > 0 && (
          <div className="flex items-center gap-4">
            <span className="text-muted-foreground">Similar examples:</span>
            <div className="flex items-center gap-2">
              {example.similars.map((similar, i) => {
                const similarExample = data.find((a) => a.href === similar);

                if (similarExample) {
                  return (
                    <Button key={i} variant="outline" className="rounded-full" asChild>
                      <Link href={"/" + similarExample.href}>
                        {similarExample.meta.title} <ExternalLinkIcon />
                      </Link>
                    </Button>
                  );
                }
              })}
            </div>
          </div>
        )}

        <ExamplePagination prevExample={prevExample} nextExample={nextExample} />
      </div>
    </>
  );
}
