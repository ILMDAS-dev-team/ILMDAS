"use client"

const languages = [
  { code: "om", label: "Afaan Oromo" },
  { code: "en", label: "English" },
  { code: "am", label: "Amharic" },
]

export function LanguageSlot() {
  return (
    <div className="language-slot" data-language-slot="true">
      {languages.map((language) => (
        <button key={language.code} type="button" lang={language.code} disabled>
          {language.label}
        </button>
      ))}
    </div>
  )
}
