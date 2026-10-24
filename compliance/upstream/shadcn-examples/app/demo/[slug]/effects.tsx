"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Logo } from "@/components/logo";

export default function Effects() {
  const [isInIframe, setIsInIframe] = useState(false);
  const params = useParams();

  useEffect(() => {
    setIsInIframe(window.top === window.self);
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const isDark = Boolean(params.get("dark"));
    document.documentElement.classList.toggle("dark", isDark);
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const iframeId = params.get("id");

    const sendHeight = () => {
      const height = document.body.scrollHeight;
      window.parent.postMessage({ type: "setHeight", height, iframeId }, "*");
    };

    sendHeight();
    const interval = setInterval(sendHeight, 300);
    setTimeout(() => clearInterval(interval), 2000);

    const observer = new ResizeObserver(sendHeight);
    observer.observe(document.body);

    if (isInIframe) {
      document.body.style.overflow = "hidden";
    }

    return () => {
      observer.disconnect();
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    const handleMessage = (e: MessageEvent) => {
      if (e.data?.type === "theme") {
        const isDark = e.data.value === "dark";
        document.documentElement.classList.toggle("dark", isDark);
      }
    };
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  if (isInIframe) {
    return (
      <div className="bg-gradient-to-b from-blue-500 to-blue-600 py-2">
        <div className="flex items-center justify-between px-4">
          <Link href="/">
            <Logo className="invert" />
          </Link>
          <div className="flex gap-3">
            <Button size="sm" asChild>
              <Link href={`/${params.slug}`}>Get Code</Link>
            </Button>
            <Button size="sm" asChild>
              <Link href="/" target="_blank">
                All Examples
              </Link>
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
