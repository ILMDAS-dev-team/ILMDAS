"use client"

import Image from "next/image"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useEffect, useState } from "react"
import { Icon } from "@/components/Icon"
import { LanguageSlot } from "@/components/LanguageSlot"
import { useLanguage } from "@/context/LanguageContext"
import { BRAND_LOGO, PROJECT_FULL_NAME, PROJECT_NAME, PROJECT_ORGANISATION } from "@/lib/brand"

export type NavLink = { href: string; label: string; translationKey?: string }

const NAV_KEYS: Record<string, string> = {
  "/": "nav.home",
  "/opac": "nav.ebooks",
  "/catalogue": "nav.catalogue",
  "/archive": "nav.archive",
  "/membership": "nav.membership",
  "/about": "nav.about",
}

export function SiteHeader({ links }: { links: NavLink[] }) {
  const pathname = usePathname()
  const { t } = useLanguage()
  const [open, setOpen] = useState(false)

  useEffect(() => {
    setOpen(false)
  }, [pathname])

  return (
    <>
      <a className="skip-link" href="#main-content">
        {t("nav.skip")}
      </a>
      <header className="site-header">
        <div className="site-header-inner">
          <Link className="brand" href="/" aria-label={`${PROJECT_FULL_NAME} home`}>
            <Image src={BRAND_LOGO} alt={`${PROJECT_NAME} logo`} width={96} height={96} priority />
            <span className="brand-text">
              <strong>{PROJECT_NAME}</strong>
              <small>{PROJECT_ORGANISATION}</small>
            </span>
          </Link>

          <button
            type="button"
            className="nav-toggle"
            aria-expanded={open}
            aria-controls="primary-navigation"
            aria-label={t("nav.menu")}
            onClick={() => setOpen((value) => !value)}
          >
            <Icon name={open ? "close" : "menu"} width={22} height={22} />
          </button>

          <nav
            id="primary-navigation"
            className={`site-nav${open ? " site-nav--open" : ""}`}
            aria-label="Public"
          >
            <ul>
              {links.map((link) => {
                const active = pathname === link.href
                return (
                  <li key={link.href}>
                    <Link href={link.href} aria-current={active ? "page" : undefined}>
                      {t(link.translationKey ?? NAV_KEYS[link.href] ?? "") || link.label}
                    </Link>
                  </li>
                )
              })}
            </ul>
          </nav>

          <div className="site-header-actions">
            <LanguageSlot />
            <Link className="button button--dark" href="/login">
              {t("nav.signIn")}
            </Link>
          </div>
        </div>
      </header>
    </>
  )
}
