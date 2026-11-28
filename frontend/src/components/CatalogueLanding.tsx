"use client"

import { SearchBar } from "@/components/SearchBar"
import { useLanguage } from "@/context/LanguageContext"

export function CatalogueLanding() {
  const { t } = useLanguage()

  return (
    <section className="simple-page">
      <h1>{t("nav.catalogue")}</h1>
      <p>{t("catalogue.description")}</p>
      <SearchBar
        label={t("catalogue.searchLabel")}
        placeholder={t("hero.searchPlaceholder")}
        buttonLabel={t("hero.searchButton")}
        variant="section"
      />
    </section>
  )
}
