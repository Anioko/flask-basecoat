import { MetadataRoute } from "next";
import data from "@/app/(site)/[slug]/data.json";

export default function sitemap(): MetadataRoute.Sitemap {
  const routesList: MetadataRoute.Sitemap = data.map((item) => ({
    url: `${process.env.BASE_URL}/${item.href}`,
    lastModified: new Date(),
    changeFrequency: "daily",
    priority: 0.5,
    images: [`${process.env.BASE_URL}/${item.info.cover_image}`]
  }));

  return [
    {
      url: `${process.env.BASE_URL}`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 0.5
    },
    ...routesList
  ];
}
