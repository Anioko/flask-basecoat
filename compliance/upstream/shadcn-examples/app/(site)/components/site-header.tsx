import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { HeaderSearch } from "@/components/search";
import Link from "next/link";
import { ThemeToggle } from "@/components/theme-toggle";
import { Logo } from "@/components/logo";
import * as React from "react";
import { GithubIcon } from "lucide-react";

export function SiteHeader() {
  return (
    <header className="bg-background/30 sticky top-0 flex h-(--header-height) shrink-0 items-center gap-2 backdrop-blur-md transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-(--header-height)">
      <div className="flex w-full items-center gap-1 px-4 lg:gap-2 lg:px-6">
        <div className="flex items-center gap-2 md:hidden">
          <Link href="/">
            <Logo />
          </Link>
          <Separator orientation="vertical" className="mx-2 data-[orientation=vertical]:h-4" />
        </div>
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mx-2 data-[orientation=vertical]:h-4" />
        <HeaderSearch />
        <div className="ml-auto flex items-center gap-1">
          <Button variant="ghost" asChild size="sm">
            <Link href="/">Home</Link>
          </Button>
          <Button variant="ghost" asChild size="sm">
            <a href="https://shadcncomponents.dev?utm_source=shadcnexamples" target="_blank">
              Components
            </a>
          </Button>
          <Button variant="ghost" asChild size="sm">
            <a href="https://github.com/shadcn-examples/shadcn-examples" target="_blank">
              <GithubIcon />
            </a>
          </Button>
          <Button variant="ghost" size="icon" asChild>
            <Link href="https://x.com/ShadcnExamples" target="_blank" className="text-foreground">
              <svg
                className="size-3.5"
                xmlns="http://www.w3.org/2000/svg"
                shapeRendering="geometricPrecision"
                textRendering="geometricPrecision"
                imageRendering="optimizeQuality"
                fillRule="evenodd"
                clipRule="evenodd"
                viewBox="0 0 512 462.799">
                <path
                  fillRule="nonzero"
                  fill="currentColor"
                  d="M403.229 0h78.506L310.219 196.04 512 462.799H354.002L230.261 301.007 88.669 462.799h-78.56l183.455-209.683L0 0h161.999l111.856 147.88L403.229 0zm-27.556 415.805h43.505L138.363 44.527h-46.68l283.99 371.278z"
                />
              </svg>
            </Link>
          </Button>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
