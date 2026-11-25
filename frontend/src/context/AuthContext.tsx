"use client"

import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { fetchCurrentUser } from "@/lib/rbac"
import type { AuthUser } from "@/lib/roles"

type AuthContextType = {
  user: AuthUser | null
  loading: boolean
  hasRole: (roleCode: string) => boolean
  isSystemAdministrator: () => boolean
  isStaff: () => boolean
  refetch: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  const loadUser = async () => {
    try {
      const current = await fetchCurrentUser()
      setUser(current)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadUser()
  }, [])

  const hasRole = (roleCode: string): boolean => {
    if (!user) return false
    return user.roles.some((r) => r.code === roleCode)
  }

  const isSystemAdministrator = (): boolean => hasRole("system_administrator")

  const isStaff = (): boolean => {
    if (!user) return false
    const staffRoles = [
      "system_administrator",
      "librarian",
      "digital_archivist",
      "journal_editor",
      "manager",
      "integration_administrator",
    ]
    return user.roles.some((r) => staffRoles.includes(r.code))
  }

  const value = {
    user,
    loading,
    hasRole,
    isSystemAdministrator,
    isStaff,
    refetch: loadUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
