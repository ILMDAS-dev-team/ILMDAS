"use client"

import { useLanguage } from "@/context/LanguageContext"
import { isLanguageCode, LANGUAGES } from "@/lib/i18n"

export function LanguageSlot() {
  const { language, setLanguage, t } = useLanguage()

  return (
    <div className="language-slot" data-language-slot="true">
      <label className="visually-hidden" htmlFor="site-language">
        {t("nav.language")}
      </label>
      <select
        id="site-language"
        value={language}
        onChange={(event) => {
          const next = event.target.value
          if (isLanguageCode(next)) setLanguage(next)
        }}
      >
        {LANGUAGES.map((item) => (
          <option key={item.code} value={item.code} lang={item.code}>
            {item.nativeLabel}
          </option>
        ))}
      </select>
    </div>
  )
}
