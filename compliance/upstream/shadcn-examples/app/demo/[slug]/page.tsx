import { Suspense } from "react";
import DemoPageGenerator from "@/app/demo/[slug]/demo-page-generator";
import data from "@/app/(site)/[slug]/data.json";
import { Metadata } from "next";

export async function generateMetadata({
  params
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;

  const example = data.find((item) => item.href === slug);

  if (!example) return {};

  return {
    title: `${example.meta.title} - Shadcn UI Examples`,
    description: example.meta.description
  };
}

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;

  const example = data.find((item) => item.href === slug);
  if (!example) return null;

  return (
    <Suspense>
      <DemoPageGenerator name={example.href} />
    </Suspense>
  );
}
