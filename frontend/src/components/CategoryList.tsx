"use client"

import Link from "next/link"
import { Icon } from "@/components/Icon"
import { useLanguage } from "@/context/LanguageContext"
import type { ResourceCategory } from "@/lib/website"

export function CategoryList({ categories }: { categories: ResourceCategory[] }) {
  const { t } = useLanguage()

  if (categories.length === 0) {
    return <p className="empty-state">{t("state.noCategories")}</p>
  }

  return (
    <ul className="category-list">
      {categories.map((category) => {
        const query = new URLSearchParams()
        query.set("category", category.slug)
        if (category.query) query.set("q", category.query)
        return (
          <li key={category.slug}>
            <Link href={`/opac?${query.toString()}`}>
              <Icon name={category.icon || "layers"} width={20} height={20} />
              <span>{category.label}</span>
            </Link>
          </li>
        )
      })}
    </ul>
  )
}
