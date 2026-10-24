import React from "react";
import data from "@/app/(site)/[slug]/data.json";
import ComponentIframe from "@/app/(site)/[slug]/components/component-iframe";
import Image from "next/image";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function Page() {
  const lastExample = data.filter((a) => a.isNew).slice(-1)[0];

  return (
    <>
      <section className="bg-linear-to-t from-transparent to-black/10 py-20 dark:to-white/15">
        <div className="mx-auto w-full max-w-3xl space-y-4 text-center">
          <a
            href={lastExample.href}
            className="group bg-muted inline-flex items-center justify-center gap-2 rounded-full border p-1 pr-3">
            <Badge className="rounded-full text-[10px] tracking-widest">NEW EXAMPLE</Badge>
            <p className="flex items-center gap-1 text-xs">
              <span>{lastExample.meta.title}</span>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                className="lucide lucide-chevron-right-icon lucide-chevron-right transition duration-300 group-hover:translate-x-0.5">
                <path d="m9 18 6-6-6-6" />
              </svg>
            </p>
          </a>
          <h1 className="text-3xl font-bold text-balance lg:text-5xl lg:leading-13">
            Reusable Shadcn UI Examples and Components
          </h1>
          <p className="text-muted-foreground text-balance lg:text-lg">
            Examples and components built with React and Tailwind CSS, compatible with Shadcn UI. It
            is open-source and includes a total of {data.length} examples and components.
          </p>
          <div className="mt-6 flex justify-center gap-2">
            <Button asChild>
              <Link href="https://github.com/shadcn-examples/shadcn-examples" target="_blank">
                Github
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link
                href="https://github.com/shadcn-examples/shadcn-examples/discussions/categories/suggestions"
                target="_blank">
                Make a suggestion
              </Link>
            </Button>
          </div>
        </div>
      </section>

      <div className="container mx-auto space-y-10 px-4">
        <div className="block lg:hidden">
          <figure className="relative aspect-video w-full">
            <Image
              src={`${process.env.BASE_URL}/${data[0].info.cover_image}`}
              fill
              alt={`shadcn examples ${data[0].meta.title}`}
            />
          </figure>
        </div>

        <div className="hidden lg:block">
          <ComponentIframe id={data[0].href} url={`/demo/${data[0].href}`} />
        </div>

        <div className="hidden lg:block">
          <ComponentIframe id={data[1].href} url={`/demo/${data[1].href}`} />
        </div>

        <div className="hidden lg:block">
          <ComponentIframe id={data[2].href} url={`/demo/${data[2].href}`} />
        </div>
      </div>
    </>
  );
}
