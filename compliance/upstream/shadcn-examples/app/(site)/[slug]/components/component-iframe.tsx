"use client";

import React, { useEffect, useRef, useState } from "react";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { useTheme } from "next-themes";
import { useIsMobile } from "@/hooks/use-mobile";
import { breakpoints, breakpointsStore, BreakpointType } from "@/store/breakpoint-store";

type ComponentIframeProps = {
  id: string;
  url?: string;
};

export default function ComponentIframe({ id, url }: ComponentIframeProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const { breakpoints: allBreakpoints } = breakpointsStore();
  const { theme } = useTheme();

  const selectedBreakpoint = allBreakpoints.find((e) => e.id === id);

  const iframeUrlSearchParams = new URLSearchParams(url);
  const customHeight = iframeUrlSearchParams.get("customHeight");

  const isMobile = useIsMobile();

  const [height, setHeight] = useState(customHeight ? customHeight + "px" : "500px");

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (
        event.data?.type === "setHeight" &&
        typeof event.data.height === "number" &&
        event.data.iframeId == id
      ) {
        setHeight(event.data.height + "px");
      }
    };

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  useEffect(() => {
    iframeRef.current?.contentWindow?.postMessage(
      {
        type: "theme",
        value: theme
      },
      "*"
    );
  }, [theme]);

  return (
    <div key={breakpoints[selectedBreakpoint?.value as "desktop" | "tablet" | "mobile"]}>
      <ResizablePanelGroup
        direction="horizontal"
        className="w-30 overflow-visible! rounded-lg border-e-0">
        <ResizablePanel
          defaultSize={breakpoints[selectedBreakpoint?.value as "desktop" | "tablet" | "mobile"]}
          minSize={34}
          className="rounded-lg border">
          <iframe
            ref={iframeRef}
            src={`${url}?id=${id}`}
            className="w-full border-0"
            style={{ height }}
          />
        </ResizablePanel>
        {!isMobile && <ResizableHandle withHandle className="bg-transparent" />}
        <ResizablePanel
          defaultSize={
            100 - breakpoints[selectedBreakpoint?.value as "desktop" | "tablet" | "mobile"]
          }></ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
