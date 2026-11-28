/**
 * Static UI copy shown while the API is unavailable or before a content team
 * publishes managed content. It describes capabilities only — no resource,
 * announcement or event is invented here.
 */

import { translate, type LanguageCode } from "@/lib/i18n"
import type { HomepagePayload, LocalizedCard } from "@/lib/website"

type FallbackCards = {
  popular: { label: string; query: string }[]
  offers: LocalizedCard[]
  learning: LocalizedCard[]
  heritage: LocalizedCard[]
}

const cards: Record<LanguageCode, FallbackCards> = {
  en: {
    popular: [
      { label: "Afaan Oromo", query: "Afaan Oromo" },
      { label: "History", query: "History" },
      { label: "Oral traditions", query: "Oral traditions" },
    ],
    offers: [
      {
        title: "Extensive Collection",
        description: "Books and research materials across subjects and languages.",
        icon: "book",
      },
      {
        title: "Digital Resources",
        description: "E-books, journals, audio and video available through digital access.",
        icon: "digital",
      },
      {
        title: "E-Books",
        description: "Browse digital books by title, author and subject through E-Book.",
        icon: "book",
      },
      {
        title: "Research & Learning",
        description: "Resources and tools that support study, inquiry and discovery.",
        icon: "research",
      },
      {
        title: "Heritage Archive",
        description: "Preserved documents, manuscripts and recordings of cultural value.",
        icon: "archive",
      },
      {
        title: "Library Resources",
        description: "E-Book records and reading materials for the ILMDAS community.",
        icon: "layers",
      },
      {
        title: "Community and Cultural Knowledge",
        description: "Knowledge shared with and for Oromo communities.",
        icon: "community",
      },
    ],
    learning: [
      {
        title: "Discover",
        description: "Find materials by title, author, subject or keyword.",
        icon: "search",
      },
      {
        title: "Research",
        description: "Follow references and explore collections for academic work.",
        icon: "research",
      },
      {
        title: "Read, Watch & Listen",
        description: "Use text, video and audio resources according to access permissions.",
        icon: "play",
      },
    ],
    heritage: [
      { title: "Historical documents", description: "", icon: "archive" },
      { title: "Oromo oral histories", description: "", icon: "audio" },
      { title: "Voices and traditions", description: "", icon: "community" },
      { title: "Research collections", description: "", icon: "research" },
      { title: "Manuscripts and records", description: "", icon: "book" },
      { title: "Cultural heritage preservation", description: "", icon: "digital" },
    ],
  },
  om: {
    popular: [
      { label: "Afaan Oromoo", query: "Afaan Oromo" },
      { label: "Seenaa", query: "History" },
      { label: "Dhugaa dubbii", query: "Oral traditions" },
    ],
    offers: [
      {
        title: "Shiboo Bala'aa",
        description: "Kitabootaa fi qannoolee mata duree fi afaanota hunda keessaa.",
        icon: "book",
      },
      {
        title: "Rakkoolee Dijitaalaa",
        description: "Kitaboonni elektroonikaa, barreeffamoonni, sagaan fi vidiyoon.",
        icon: "digital",
      },
      {
        title: "Kitaboota Elektroonikaa",
        description:
          "Kitaboota dijitaalaa maqa'aa, barreessaa fi mata dureen Kitaboo Elektroonikaa keessa barbaadi.",
        icon: "book",
      },
      {
        title: "Qorannoo fi Barannoo",
        description: "Rakkoolee fi meeshaaleen barannoo fi qorannoo deeggaru.",
        icon: "research",
      },
      {
        title: "Arkiiivii Dhaalaa",
        description: "Dokumeentii, hujaa fi sagaan aadaa eeggame.",
        icon: "archive",
      },
      {
        title: "Rakkoolee Mana Kitabaa",
        description: "Rakkoolee Kitaboo Elektroonikaa fi kitaboota hawaasa ILMDASaf dhaala ta'u.",
        icon: "layers",
      },
      {
        title: "Beekumsa Hawaasa fi Aadaa",
        description: "Beekumsa hawaasa Oromoo waliin qoodamuu.",
        icon: "community",
      },
    ],
    learning: [
      {
        title: "Barba'uu",
        description: "Maqa'aa, barreessaa, mata duree ykn jechaan argachuu.",
        icon: "search",
      },
      {
        title: "Qorannoo",
        description: "Madda hordofuun shiboo qorannoo keessa darbuu.",
        icon: "research",
      },
      {
        title: "Dubbisuu, Daaw'uu fi Dhageettii",
        description: "Barreeffama, vidiyoo fi sagaa darbii eegamusaatiin fayyadamuu.",
        icon: "play",
      },
    ],
    heritage: [
      { title: "Dokumeentii seenaa", description: "", icon: "archive" },
      { title: "Dhugaa dubbii Oromoo", description: "", icon: "audio" },
      { title: "Sagaa fi aadaa", description: "", icon: "community" },
      { title: "Shiboo qorannoo", description: "", icon: "research" },
      { title: "Hujaa fi galii", description: "", icon: "book" },
      { title: "Eeggannoo dhaala aadaa", description: "", icon: "digital" },
    ],
  },
  am: {
    popular: [
      { label: "ኦሮሞ ቋንቋ", query: "Afaan Oromo" },
      { label: "ታሪክ", query: "History" },
      { label: "የአፍ ቃል ወጎች", query: "Oral traditions" },
    ],
    offers: [
      {
        title: "ሰፊ ስብስብ",
        description: " በተለያዩ ርዕሰ ጉዳዮችና ቋንቋዎች ያሉ መጻሕፍትና የምርምር ቁሳቁሶች።",
        icon: "book",
      },
      {
        title: "ዲጂታል ሀብቶች",
        description: "በዲጂታል መዳረሻ የሚገኙ መጻሕፍት፣ ጆርናሎች፣ ድምፆችና ቪዲዮዎች።",
        icon: "digital",
      },
      {
        title: "የኤሌክትሮኒክ መጻሕፍት",
        description: "ዲጂታል መጻሕፍትን በርዕስ፣ በደራሲና በርዕሰ ጉዳይ በኤሌክትሮኒክ መጻሕፍት ውስጥ ይፈልጉ።",
        icon: "book",
      },
      {
        title: "ምርምርና መማር",
        description: "ማጥናትን፣ መፈለግንና ማግኘትን የሚደግፉ ቁሳቁሶች።",
        icon: "research",
      },
      {
        title: "የቅርስ ማህደር",
        description: "የባህል ዋጋ ያላቸው ሰነዶች፣ ጥንታዊ ጽሑፎችና ቀረጻዎች።",
        icon: "archive",
      },
      {
        title: "የቤተመጻሕፍት ሀብቶች",
        description: "ለ ILMDAS ማህበረሰብ የሚገኙ የኤሌክትሮኒክ መጻሕፍት መዝገቦችና የንባብ ቁሳቁሶች።",
        icon: "layers",
      },
      {
        title: "የማህበረሰብና የባህል እውቀት",
        description: "ከኦሮሞ ማህበረሰብ ጋር የሚጋራ እውቀት።",
        icon: "community",
      },
    ],
    learning: [
      {
        title: "ማግኘት",
        description: "በርዕስ፣ በደራሲ፣ በርዕሰ ጉዳይ ወይም በቁልፍ ቃል መፈለግ።",
        icon: "search",
      },
      {
        title: "ምርምር",
        description: "ማጣቀሻዎችን ተከትለው ስብስቦችን ማሰስ።",
        icon: "research",
      },
      {
        title: "ማንበብ፣ ማየትና ማዳመጥ",
        description: "የጽሑፍ፣ የቪዲዮና የድምፅ ሀብቶችን በመዳረሻ ፈቃዳቸው መጠቀም።",
        icon: "play",
      },
    ],
    heritage: [
      { title: "የታሪክ ሰነዶች", description: "", icon: "archive" },
      { title: "የኦሮሞ አፍ ቃል ታሪኮች", description: "", icon: "audio" },
      { title: "ድምፆችና ወጎች", description: "", icon: "community" },
      { title: "የምርምር ስብስቦች", description: "", icon: "research" },
      { title: "ጥንታዊ ጽሑፎችና መዝገቦች", description: "", icon: "book" },
      { title: "የባህል ቅርስ ጥበቃ", description: "", icon: "digital" },
    ],
  },
}

export function fallbackHomepage(language: LanguageCode): HomepagePayload {
  const content = cards[language]
  const section = (kind: "offer" | "learning" | "heritage") => ({
    title: translate(language, `section.${kind}.title`),
    subtitle: translate(language, `section.${kind}.subtitle`),
    cards: content[kind === "offer" ? "offers" : kind],
  })
  return {
    language,
    hero: {
      eyebrow: [
        translate(language, "hero.eyebrow.discover"),
        translate(language, "hero.eyebrow.learn"),
        translate(language, "hero.eyebrow.preserve"),
      ].join(" · "),
      title: translate(language, "hero.title"),
      description: translate(language, "hero.description"),
      searchLabel: translate(language, "hero.searchLabel"),
      searchPlaceholder: translate(language, "hero.searchPlaceholder"),
      popularSearches: content.popular,
      archiveFeature: {
        title: translate(language, "hero.archiveTitle"),
        description: translate(language, "hero.archiveDescription"),
        path: "/archive",
      },
    },
    offers: section("offer"),
    heritage: section("heritage"),
    learning: section("learning"),
    categories: [
      {
        label: translate(language, "category.ebooks"),
        slug: "ebooks",
        description: "",
        icon: "book",
        query: "ebook",
      },
    ],
    featuredResources: [],
    updates: [],
    membership: {
      title: translate(language, "section.membership.title"),
      description: translate(language, "section.membership.description"),
      path: "/membership",
    },
    footer: {
      description: translate(language, "footer.description"),
      groups: {
        quick_links: [
          { label: translate(language, "nav.home"), url: "/", icon: "" },
          { label: translate(language, "nav.ebooks"), url: "/opac", icon: "" },
          { label: translate(language, "nav.catalogue"), url: "/catalogue", icon: "" },
          { label: translate(language, "nav.archive"), url: "/archive", icon: "" },
          { label: translate(language, "nav.membership"), url: "/membership", icon: "" },
          { label: translate(language, "nav.about"), url: "/about", icon: "" },
        ],
        resources: [],
        connect: [],
      },
    },
  }
}

/** Use published API content where present and approved UI copy otherwise. */
export function resolveHomepage(data: HomepagePayload, language: LanguageCode): HomepagePayload {
  const fallback = fallbackHomepage(language)
  const section = (
    apiSection: HomepagePayload["offers"],
    fallbackSection: HomepagePayload["offers"]
  ) => ({
    title: apiSection.title || fallbackSection.title,
    subtitle: apiSection.subtitle || fallbackSection.subtitle,
    cards: apiSection.cards.length > 0 ? apiSection.cards : fallbackSection.cards,
  })
  return {
    ...data,
    language,
    hero: {
      ...fallback.hero,
      ...data.hero,
      title: data.hero.title || fallback.hero.title,
      description: data.hero.description || fallback.hero.description,
      searchLabel: data.hero.searchLabel || fallback.hero.searchLabel,
      searchPlaceholder: data.hero.searchPlaceholder || fallback.hero.searchPlaceholder,
      eyebrow: data.hero.eyebrow || fallback.hero.eyebrow,
      popularSearches:
        data.hero.popularSearches.length > 0
          ? data.hero.popularSearches
          : fallback.hero.popularSearches,
      archiveFeature: {
        title: data.hero.archiveFeature.title || fallback.hero.archiveFeature.title,
        description:
          data.hero.archiveFeature.description || fallback.hero.archiveFeature.description,
        path: data.hero.archiveFeature.path || fallback.hero.archiveFeature.path,
      },
    },
    offers: section(data.offers, fallback.offers),
    heritage: section(data.heritage, fallback.heritage),
    learning: section(data.learning, fallback.learning),
    categories: data.categories.length > 0 ? data.categories : fallback.categories,
    membership: {
      title: data.membership.title || fallback.membership.title,
      description: data.membership.description || fallback.membership.description,
      path: data.membership.path || fallback.membership.path,
    },
    footer: {
      description: data.footer.description || fallback.footer.description,
      groups: {
        ...fallback.footer.groups,
        ...data.footer.groups,
      },
    },
  }
}
