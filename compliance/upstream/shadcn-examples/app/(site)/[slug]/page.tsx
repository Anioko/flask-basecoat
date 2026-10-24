import data from "@/app/(site)/[slug]/data.json";
import { Metadata } from "next";
import ExampleDetail from "@/app/(site)/[slug]/components/example-detail";
import { Example } from "@/types/example";

export async function generateMetadata({
  params
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;

  const example = data.find((item) => item.href === slug);

  if (!example) return {};

  return {
    title: `${example.meta.title} - Shadcn UI Examples and Components`,
    description: example.meta.description
  };
}

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;

  const exampleData: Example | undefined = data.find((item) => item.href === slug);

  if (!exampleData) return null;

  return <ExampleDetail example={exampleData} />;
}
