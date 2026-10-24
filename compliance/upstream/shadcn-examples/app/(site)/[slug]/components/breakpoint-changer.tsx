"use client";

import React, { useState } from "react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Monitor, Smartphone, Tablet } from "lucide-react";
import { breakpointsStore } from "@/store/breakpoint-store";
import { useIsMobile } from "@/hooks/use-mobile";

export default function BreakpointChanger({ id }: { id: string }) {
  const { setBreakpoint } = breakpointsStore();
  const [value, setValue] = useState<string>("desktop");

  const handleBreakpointChange = (value: string) => {
    setBreakpoint({ id, value });
    setValue(value);
  };

  const isMobile = useIsMobile();

  if (isMobile) return null;

  return (
    <>
      <ToggleGroup
        type="single"
        className="bg-background border"
        value={value}
        onValueChange={(v) => handleBreakpointChange(v)}>
        <Tooltip>
          <TooltipTrigger asChild>
            <ToggleGroupItem value="mobile">
              <Smartphone />
            </ToggleGroupItem>
          </TooltipTrigger>
          <TooltipContent>
            <p>Mobile</p>
          </TooltipContent>
        </Tooltip>
        <ToggleGroupItem value="tablet">
          <Tooltip>
            <TooltipTrigger asChild>
              <ToggleGroupItem value="bold">
                <Tablet />
              </ToggleGroupItem>
            </TooltipTrigger>
            <TooltipContent>
              <p>Tablet</p>
            </TooltipContent>
          </Tooltip>
        </ToggleGroupItem>
        <ToggleGroupItem value="desktop">
          <Tooltip>
            <TooltipTrigger asChild>
              <ToggleGroupItem value="desktop">
                <Monitor />
              </ToggleGroupItem>
            </TooltipTrigger>
            <TooltipContent>
              <p>Desktop</p>
            </TooltipContent>
          </Tooltip>
        </ToggleGroupItem>
      </ToggleGroup>
    </>
  );
}
