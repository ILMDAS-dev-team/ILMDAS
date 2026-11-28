import { fallbackHomepage, resolveHomepage } from "@/lib/homepageContent"
import type { HomepagePayload } from "@/lib/website"

test("fallback copy describes capabilities without inventing resources", () => {
  const fallback = fallbackHomepage("en")
  expect(fallback.hero.title).toBe("A world of knowledge. A heritage to keep.")
  expect(fallback.offers.cards).toHaveLength(7)
  expect(fallback.offers.cards.map((card) => card.title)).toContain("E-Books")
  expect(fallback.learning.cards).toHaveLength(3)
  expect(fallback.categories).toEqual([
    { label: "E-Books", slug: "ebooks", description: "", icon: "book", query: "ebook" },
  ])
  expect(fallback.featuredResources).toEqual([])
  expect(fallback.updates).toEqual([])
})

test("published API content replaces empty fallback sections", () => {
  const apiPayload: HomepagePayload = {
    ...fallbackHomepage("en"),
    hero: {
      ...fallbackHomepage("en").hero,
      title: "Managed hero title",
      popularSearches: [{ label: "Culture", query: "Culture" }],
    },
    categories: [{ label: "E-books", slug: "ebooks", description: "", icon: "book", query: "" }],
    updates: [
      {
        id: 1,
        kind: "announcement",
        title: "Approved announcement",
        summary: "",
        detailPath: "",
        imagePath: "",
        publishedAt: "2026-01-01T00:00:00Z",
        eventDate: null,
      },
    ],
  }

  const resolved = resolveHomepage(apiPayload, "en")
  expect(resolved.hero.title).toBe("Managed hero title")
  expect(resolved.hero.popularSearches).toEqual([{ label: "Culture", query: "Culture" }])
  expect(resolved.categories).toHaveLength(1)
  expect(resolved.updates).toHaveLength(1)
  expect(resolved.offers.cards).toHaveLength(7)
})

test("E-Books stays available when no categories are published", () => {
  const payload = { ...fallbackHomepage("en"), categories: [] }
  const resolved = resolveHomepage(payload, "en")

  expect(resolved.categories).toHaveLength(1)
  expect(resolved.categories[0].label).toBe("E-Books")
  expect(resolved.categories[0].query).toBe("ebook")
})
