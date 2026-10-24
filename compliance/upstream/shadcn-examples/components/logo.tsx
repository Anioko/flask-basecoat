import Image from "next/image";
import { cn } from "@/lib/utils";

export function Logo({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center justify-center gap-2", className)}>
      <div className="relative size-5">
        <Image
          className="dark:invert"
          src={`${process.env.NEXT_PUBLIC_BASE_URL}/logo.png`}
          fill
          alt="shadcn examples logo"
        />
      </div>
      <span className="hidden font-medium md:inline">Shadcn Examples</span>
    </div>
  );
}
