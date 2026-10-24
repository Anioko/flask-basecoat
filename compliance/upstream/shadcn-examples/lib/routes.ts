export const routes = [
  {
    url: `/`,
    meta: {
      title: "shadcn/ui Examples",
      description: "Shadcn UI examples for your project. Get the code and add it to your project.",
      image: ""
    }
  },
  {
    url: `/mail-app`,
    meta: {
      title: "Music App",
      description: "",
      image: ""
    }
  },
  {
    url: `/music-app`,
    meta: {
      title: "Music App",
      description: "",
      image: ""
    }
  }
] as const;

export type Route = (typeof routes)[number];
