"use client"

import Link from "next/link"
import { redirect } from "next/navigation"
import { useEffect, useState, type ReactNode } from "react"
import { useAuth } from "@/context/AuthContext"
import AccessDenied from "@/components/AccessDenied"
import { LanguageSlot } from "@/components/LanguageSlot"
import { isSystemAdministrator, isStaff } from "@/lib/roles"

const baseLinks = [
  { href: "/staff", label: "Home" },
  { href: "/staff/catalogue", label: "Catalogue" },
  { href: "/staff/circulation", label: "Circulation" },
  { href: "/staff/membership", label: "Membership" },
  { href: "/staff/archive", label: "Archive" },
  { href: "/staff/publishing", label: "Publishing" },
  { href: "/staff/reports", label: "Reports" },
  { href: "/staff/administration", label: "Administration" },
  { href: "/staff/status", label: "IIIF status" },
  { href: "/logout", label: "Sign out" },
]

export default function StaffLayout({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  const [links, setLinks] = useState(baseLinks)

  useEffect(() => {
    if (loading || !user) return
    const admin = isSystemAdministrator(user)
    const staff = isStaff(user)
    const filtered = baseLinks.filter((link) => {
      if (link.href === "/staff/administration") return admin
      return staff
    })
    setLinks(filtered)
  }, [loading, user])

  // Do not render children when loading or unauthenticated
  if (loading) {
    return (
      <div className="shell">
        <p>Loading...</p>
      </div>
    )
  }

  if (!user) {
    redirect("/login?next=/staff")
  }

  // Signed in without a staff role: show the denial instead of looping back to login.
  if (!isStaff(user)) {
    return (
      <div className="shell">
        <AccessDenied />
      </div>
    )
  }

  return (
    <div className="shell" data-shell="staff">
      <header>
        <p>ILMDAS staff</p>
        <nav className="nav" aria-label="Staff">
          {links.map((link) => (
            <Link key={link.href} href={link.href}>
              {link.label}
            </Link>
          ))}
        </nav>
        <LanguageSlot />
      </header>
      <main>{children}</main>
    </div>
  )
}
