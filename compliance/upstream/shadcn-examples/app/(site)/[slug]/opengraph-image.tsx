import { ImageResponse } from "next/og";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { Example } from "@/types/example";
import data from "@/app/(site)/[slug]/data.json";

export const size = {
  width: 1200,
  height: 630
};

function arrayBufferToBase64(buffer: ArrayBuffer) {
  const binary = String.fromCharCode(...new Uint8Array(buffer));
  return `data:image/png;base64,${Buffer.from(binary, "binary").toString("base64")}`;
}

export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const exampleData: Example | undefined = data.find((item) => item.href === slug);

  const interSemiBold = await readFile(join(process.cwd(), "assets/Inter/Inter_28pt-SemiBold.ttf"));

  const logoSrc = await fetch(new URL("logo.png", process.env.BASE_URL)).then((res) =>
    res.arrayBuffer()
  );

  const logoBase64 = arrayBufferToBase64(logoSrc);

  if (!exampleData) return null;

  return new ImageResponse(
    (
      <div
        tw="bg-black text-white"
        style={{
          height: "100%",
          width: "100%",
          display: "flex",
          textAlign: "center",
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
          flexWrap: "nowrap"
        }}>
        <div
          style={{
            display: "flex",
            position: "absolute",
            alignItems: "center",
            top: 30,
            left: 30,
            gap: 20
          }}>
          <div tw="invert bg-white/80 p-2 rounded-lg flex">
            <img width={36} height={36} src={logoBase64} />
          </div>
          <span style={{ fontSize: 28 }}>shadcnexamples.com</span>
        </div>
        <div
          tw="font-bold text-5xl mb-8"
          style={{
            display: "flex",
            marginTop: 30,
            whiteSpace: "pre-wrap"
          }}>
          <b>{exampleData.meta.title}</b>
        </div>
        <div
          tw="text-white/70 text-2xl max-w-3xl"
          style={{
            display: "flex",
            fontStyle: "normal",
            whiteSpace: "pre-wrap"
          }}>
          <b>{exampleData.info.description}</b>
        </div>
        <div tw="ml-3 mt-14 flex ">
          <a tw="flex gap-3 items-center justify-center bg-white rounded-lg px-7 py-4 text-base font-medium text-black">
            Preview Example <span style={{ display: "flex", marginLeft: "10px" }}>&#62;</span>
          </a>
        </div>
      </div>
    ),
    {
      ...size,
      fonts: [
        {
          name: "Inter",
          data: interSemiBold,
          style: "normal",
          weight: 400
        }
      ]
    }
  );
}
