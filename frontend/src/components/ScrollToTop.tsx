"use client"

import { useEffect, useState } from "react"
import { Icon } from "@/components/Icon"
import { useLanguage } from "@/context/LanguageContext"

const VISIBLE_AFTER = 320

export function ScrollToTop() {
  const { t } = useLanguage()
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > VISIBLE_AFTER)
    onScroll()
    window.addEventListener("scroll", onScroll, { passive: true })
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  if (!visible) return null

  const scrollToTop = () => {
    const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches
    window.scrollTo({ top: 0, behavior: reducedMotion ? "auto" : "smooth" })
  }

  return (
    <button
      type="button"
      className="scroll-to-top"
      aria-label={t("nav.backToTop")}
      title={t("nav.backToTop")}
      onClick={scrollToTop}
    >
      <Icon name="up" width={22} height={22} />
    </button>
  )
}
