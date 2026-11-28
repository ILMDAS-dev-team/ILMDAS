/** Types and API access for the public ILMDAS homepage. */

import { apiFetch } from "@/lib/api"
import type { LanguageCode } from "@/lib/i18n"

export type LocalizedCard = {
  id?: number
  title: string
  description: string
  icon: string
  linkLabel?: string
  linkPath?: string
}

export type HomeSection = {
  title: string
  subtitle: string
  cards: LocalizedCard[]
}

export type PopularSearch = { label: string; query: string }

export type ResourceCategory = {
  label: string
  slug: string
  description: string
  icon: string
  query: string
}

export type FeaturedResource = {
  id?: number
  title: string
  resourceType: string
  source: string
  sourceId: string
  description: string
  detailPath: string
  thumbnailPath: string
  accessStatus: string
}

export type InstitutionalUpdate = {
  id?: number
  kind: string
  title: string
  summary: string
  detailPath: string
  imagePath: string
  publishedAt: string
  eventDate: string | null
}

export type FooterLink = { label: string; url: string; icon: string }

export type HomepagePayload = {
  language: string
  hero: {
    eyebrow: string
    title: string
    description: string
    searchLabel: string
    searchPlaceholder: string
    popularSearches: PopularSearch[]
    archiveFeature: { title: string; description: string; path: string }
  }
  offers: HomeSection
  heritage: HomeSection
  learning: HomeSection
  categories: ResourceCategory[]
  featuredResources: FeaturedResource[]
  updates: InstitutionalUpdate[]
  membership: { title: string; description: string; path: string }
  footer: { description: string; groups: Record<string, FooterLink[]> }
}

/** Fetch approved public homepage content from the existing Django API. */
export async function fetchHomepage(language: LanguageCode): Promise<HomepagePayload> {
  const { response } = await apiFetch(`/api/v1/website/home/?lang=${encodeURIComponent(language)}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch homepage: ${response.status}`)
  }
  const payload = (await response.json()) as HomepagePayload
  if (!payload || !payload.hero || !payload.offers || !payload.footer) {
    throw new Error("Invalid homepage payload")
  }
  return payload
}
