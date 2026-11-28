"use client"

import Image from "next/image"
import Link from "next/link"
import { SocialLinks } from "@/components/SocialLinks"
import { useLanguage } from "@/context/LanguageContext"
import { useWebsite } from "@/context/WebsiteContext"
import { BRAND_LOGO, PROJECT_NAME, PROJECT_ORGANISATION } from "@/lib/brand"
import type { FooterLink } from "@/lib/website"

export function SiteFooter() {
  const { t } = useLanguage()
  const { homepage } = useWebsite()
  const groups = homepage.footer.groups

  const group = (key: string, title: string, links: FooterLink[] | undefined) => {
    if (!links || links.length === 0) return null
    return (
      <div className="footer-column">
        <h2>{title}</h2>
        <ul>
          {links.map((link) => (
            <li key={`${link.url}-${link.label}`}>
              {link.url.startsWith("http") ? (
                <a href={link.url} rel="noopener noreferrer" target="_blank">
                  {link.label}
                </a>
              ) : (
                <Link href={link.url}>{link.label}</Link>
              )}
            </li>
          ))}
        </ul>
      </div>
    )
  }

  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <Image src={BRAND_LOGO} alt={`${PROJECT_NAME} logo`} width={96} height={96} />
          <strong>{PROJECT_NAME}</strong>
          <small>{PROJECT_ORGANISATION}</small>
          <p>{homepage.footer.description || t("footer.description")}</p>
          <SocialLinks className="footer-social" />
        </div>
        {group("quick_links", t("footer.quickLinks"), groups.quick_links)}
        {group("resources", t("footer.resources"), groups.resources)}
        {group("connect", t("footer.connect"), groups.connect)}
      </div>
      <div className="footer-bottom">
        <span>
          © {new Date().getFullYear()} {PROJECT_NAME}. {t("footer.rights")}
        </span>
        <Link href={homepage.membership.path || "/membership"}>{t("nav.membership")}</Link>
      </div>
    </footer>
  )
}
