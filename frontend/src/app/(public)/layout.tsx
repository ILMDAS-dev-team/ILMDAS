import type { ReactNode } from "react"
import { LanguageSlot } from "@/components/LanguageSlot"

const links = [
  { href: "/", label: "Home" },
  { href: "/opac", label: "OPAC" },
  { href: "/about", label: "About" },
]

export default function PublicLayout({ children }: { children: ReactNode }) {
  return (
    <div className="shell" data-shell="public">
      <header>
        <p>IQQO public catalogue</p>
        <nav className="nav" aria-label="Public">
          {links.map((link) => (
            <a key={link.href} href={link.href}>
              {link.label}
            </a>
          ))}
        </nav>
        <LanguageSlot />
      </header>
      <main>{children}</main>
    </div>
  )
}
