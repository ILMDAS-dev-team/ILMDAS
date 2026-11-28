"use client"

import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { useLanguage } from "@/context/LanguageContext"
import { fallbackHomepage, resolveHomepage } from "@/lib/homepageContent"
import { fetchHomepage, type HomepagePayload } from "@/lib/website"

type WebsiteContextType = {
  homepage: HomepagePayload
  status: "loading" | "ready" | "error"
}

const WebsiteContext = createContext<WebsiteContextType | null>(null)

export function WebsiteProvider({ children }: { children: ReactNode }) {
  const { language } = useLanguage()
  const [homepage, setHomepage] = useState<HomepagePayload>(() => fallbackHomepage("en"))
  const [status, setStatus] = useState<WebsiteContextType["status"]>("loading")

  useEffect(() => {
    let cancelled = false
    setHomepage(fallbackHomepage(language))
    setStatus("loading")
    fetchHomepage(language)
      .then((data) => {
        if (!cancelled) {
          setHomepage(resolveHomepage(data, language))
          setStatus("ready")
        }
      })
      .catch(() => {
        if (!cancelled) setStatus("error")
      })
    return () => {
      cancelled = true
    }
  }, [language])

  return <WebsiteContext.Provider value={{ homepage, status }}>{children}</WebsiteContext.Provider>
}

export function useWebsite(): WebsiteContextType {
  const context = useContext(WebsiteContext)
  if (!context) {
    throw new Error("useWebsite must be used within a WebsiteProvider")
  }
  return context
}
