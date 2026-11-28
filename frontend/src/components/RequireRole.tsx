"use client"

import { useEffect, useState, type ReactNode } from "react"
import { useAuth } from "@/context/AuthContext"
import AccessDenied from "@/components/AccessDenied"
import { hasAnyRole, hasRole, isStaff } from "@/lib/roles"

type RequireRoleProps = {
  children: ReactNode
  role?: string
  /** Allow the user if they hold any one of these roles. */
  anyRole?: string[]
  requireStaff?: boolean
}

export function RequireRole({ children, role, anyRole, requireStaff = false }: RequireRoleProps) {
  const { user, loading } = useAuth()
  const [authorized, setAuthorized] = useState<boolean | null>(null)
  const anyRoleKey = anyRole?.join(",")

  useEffect(() => {
    if (loading) {
      setAuthorized(null)
      return
    }
    if (!user) {
      setAuthorized(false)
      return
    }
    if (role) {
      setAuthorized(hasRole(user, role))
    } else if (anyRoleKey) {
      setAuthorized(hasAnyRole(user, anyRoleKey.split(",")))
    } else if (requireStaff) {
      setAuthorized(isStaff(user))
    } else {
      setAuthorized(true)
    }
  }, [loading, user, role, anyRoleKey, requireStaff])

  if (loading || authorized === null) {
    return (
      <section>
        <p>Loading...</p>
      </section>
    )
  }

  if (!authorized) {
    return <AccessDenied />
  }

  return <>{children}</>
}
