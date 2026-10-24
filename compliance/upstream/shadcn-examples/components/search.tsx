"use client";

import * as React from "react";
import { CircleDotDashedIcon, SearchIcon } from "lucide-react";

import {
  CommandDialog,
  CommandEmpty,
  CommandInput,
  CommandItem,
  CommandList
} from "@/components/ui/command";
import { Input } from "@/components/ui/input";
import data from "@/app/(site)/[slug]/data.json";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function HeaderSearch() {
  const [open, setOpen] = React.useState(false);
  const router = useRouter();

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  return (
    <>
      <div className="lg:*:not-first:mt-2">
        <div className="relative hidden lg:flex">
          <Input
            className="peer ps-9 pe-9"
            placeholder="Search examples..."
            type="search"
            onFocusCapture={() => setOpen(true)}
          />
          <div className="text-muted-foreground/80 pointer-events-none absolute inset-y-0 start-0 flex items-center justify-center ps-3 peer-disabled:opacity-50">
            <SearchIcon size={16} />
          </div>
        </div>
        <div className="relative flex lg:hidden">
          <Button variant="ghost" onClick={() => setOpen(true)}>
            <SearchIcon />
          </Button>
        </div>
      </div>
      <CommandDialog open={open} onOpenChange={setOpen}>
        <CommandInput placeholder="Search in list" />
        <CommandList>
          <CommandEmpty>No results found.</CommandEmpty>
          {data.map((item, i) => (
            <CommandItem
              key={i}
              disabled={!!item?.isComing}
              onSelect={() => {
                if (item.href) {
                  setOpen(false);
                  router.push(item.href);
                }
              }}>
              <CircleDotDashedIcon />
              <span>{item.meta.title}</span>
              {item?.isComing ? <Badge className="ms-2 bg-orange-600">Coming Soon</Badge> : null}
              {item?.isNew ? <Badge className="bg-green-600">New</Badge> : false}
            </CommandItem>
          ))}
        </CommandList>
      </CommandDialog>
    </>
  );
}
