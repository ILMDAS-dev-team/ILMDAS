"use client"

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react"
import { isLanguageCode, LANGUAGE_COOKIE, translate, type LanguageCode } from "@/lib/i18n"

type LanguageContextType = {
  language: LanguageCode
  setLanguage: (language: LanguageCode) => void
  t: (key: string) => string
}

const LanguageContext = createContext<LanguageContextType | null>(null)

function readCookie(): LanguageCode {
  if (typeof document === "undefined") return "en"
  const match = document.cookie
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${LANGUAGE_COOKIE}=`))
  const value = match?.slice(LANGUAGE_COOKIE.length + 1)
  return isLanguageCode(value) ? value : "en"
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<LanguageCode>("en")

  useEffect(() => {
    const saved = readCookie()
    setLanguageState(saved)
    document.documentElement.lang = saved
  }, [])

  const setLanguage = useCallback((next: LanguageCode) => {
    setLanguageState(next)
    document.cookie = `${LANGUAGE_COOKIE}=${next}; path=/; max-age=31536000; samesite=lax`
    document.documentElement.lang = next
  }, [])

  const t = useCallback((key: string) => translate(language, key), [language])

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage(): LanguageContextType {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider")
  }
  return context
}
