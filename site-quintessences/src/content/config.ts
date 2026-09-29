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

// La collection Galerie reste volontairement absente tant que le processus
// de vérification vie privée et de publication des médias n'est pas validé.
export const collections = { actualites };
