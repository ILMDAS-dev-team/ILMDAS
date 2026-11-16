import type { ReactNode } from "react"
import { LanguageSlot } from "@/components/LanguageSlot"

const links = [
  { href: "/staff", label: "Home" },
  { href: "/staff/catalogue", label: "Catalogue" },
  { href: "/staff/circulation", label: "Circulation" },
  { href: "/staff/membership", label: "Membership" },
  { href: "/staff/archive", label: "Archive" },
  { href: "/staff/publishing", label: "Publishing" },
  { href: "/staff/reports", label: "Reports" },
  { href: "/staff/administration", label: "Administration" },
  { href: "/staff/status", label: "IIIF status" },
]

export default function StaffLayout({ children }: { children: ReactNode }) {
  return (
    <div className="shell" data-shell="staff">
      <header>
        <p>ILMDAS staff</p>
        <nav className="nav" aria-label="Staff">
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
