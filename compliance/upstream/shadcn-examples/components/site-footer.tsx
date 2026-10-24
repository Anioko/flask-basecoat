import { Logo } from "@/components/logo";
import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between gap-8">
          <div className="flex flex-col gap-4 md:max-w-96">
            <div className="flex items-center gap-2">
              <Logo />
            </div>
          </div>

          <div className="md:ms-auto md:max-w-96">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-muted-foreground text-xs">
                © {new Date().getFullYear()}{" "}
                <Link href="/" className="hover:underline">
                  Shadcn Examples
                </Link>
                . <span className="hidden md:inline">All rights reserved.</span>
              </p>
            </div>
          </div>
        </div>
        <div className="mt-4">
          <a
            href="https://startupfa.me/s/shadcn-examples?utm_source=shadcnexamples.com"
            target="_blank">
            <img
              src="https://startupfa.me/badges/featured/dark-small-rounded.webp"
              alt="Featured on Startup Fame"
              width="240"
              height="37"
            />
          </a>
        </div>
      </div>
    </footer>
  );
}
