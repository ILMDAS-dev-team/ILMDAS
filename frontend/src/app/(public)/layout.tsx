import type { ReactNode } from "react"
import { ScrollToTop } from "@/components/ScrollToTop"
import { SiteFooter } from "@/components/SiteFooter"
import { SiteHeader } from "@/components/SiteHeader"
import { WebsiteProvider } from "@/context/WebsiteContext"

const links = [
  { href: "/", label: "Home", translationKey: "nav.home" },
  { href: "/opac", label: "E-Book", translationKey: "nav.ebooks" },
  { href: "/catalogue", label: "Catalogue", translationKey: "nav.catalogue" },
  { href: "/archive", label: "Archive", translationKey: "nav.archive" },
  { href: "/membership", label: "Membership", translationKey: "nav.membership" },
  { href: "/about", label: "About", translationKey: "nav.about" },
]

export default function PublicLayout({ children }: { children: ReactNode }) {
  return (
    <div className="public-site" data-shell="public">
      <WebsiteProvider>
        <SiteHeader links={links} />
        <main id="main-content" className="shell">
          {children}
        </main>
        <SiteFooter />
        <ScrollToTop />
      </WebsiteProvider>
    </div>
  )
}
