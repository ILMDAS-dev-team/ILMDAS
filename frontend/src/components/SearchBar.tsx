"use client"

import Link from "next/link"
import { useLanguage } from "@/context/LanguageContext"
import type { PopularSearch } from "@/lib/website"

type SearchBarProps = {
  label: string
  placeholder: string
  buttonLabel: string
  popularSearches?: PopularSearch[]
  category?: string
  variant?: "hero" | "section"
}

/** Searches the existing OPAC route; no duplicate search implementation. */
export function SearchBar({
  label,
  placeholder,
  buttonLabel,
  popularSearches = [],
  category,
  variant = "hero",
}: SearchBarProps) {
  const { t } = useLanguage()
  return (
    <div className={`search-bar search-bar--${variant}`}>
      <form action="/opac" method="get" role="search">
        <label className="search-bar-label" htmlFor={`search-${variant}`}>
          {label}
        </label>
        <div className="search-bar-row">
          <input
            id={`search-${variant}`}
            name="q"
            type="search"
            placeholder={placeholder}
            autoComplete="off"
          />
          {category ? <input type="hidden" name="category" value={category} /> : null}
          <button type="submit">{buttonLabel}</button>
        </div>
      </form>
      {popularSearches.length > 0 ? (
        <p className="popular-searches">
          <span>{t("hero.popular")}</span>
          {popularSearches.map((item) => (
            <Link
              key={`${item.label}-${item.query}`}
              href={`/opac?q=${encodeURIComponent(item.query)}`}
            >
              {item.label}
            </Link>
          ))}
        </p>
      ) : null}
    </div>
  )
}
