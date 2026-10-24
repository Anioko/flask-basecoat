"use client";

import React from "react";
import { useCodeCopyStore } from "@/store/use-copy-code";
import CodeBlock from "@/components/code-renderer";

export default function TabCodePreview() {
  const { code } = useCodeCopyStore();

  return <CodeBlock code={code} lang="tsx" />;
}
