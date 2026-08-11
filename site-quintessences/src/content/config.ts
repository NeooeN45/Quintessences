import { defineCollection, z } from "astro:content";

// SITE-D-001 : contenu versionné dans le dépôt, pas de CMS tiers.
const actualites = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    summary: z.string(),
    app: z
      .enum([
        "geosylva",
        "ignis",
        "hydro",
        "flora",
        "artemis",
        "qgisia",
        "terra",
        "aeris",
        "atlas",
      ])
      .optional(),
  }),
});

// SITE-F-018 à SITE-F-021 : chaque média porte une légende, une date,
// un contexte et une mention explicite si ce n'est pas une opération réelle.
const galerie = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    context: z.string(),
    app: z.string().optional(),
    mediaUrl: z.string(),
    isDemo: z.boolean(),
  }),
});

export const collections = { actualites, galerie };
