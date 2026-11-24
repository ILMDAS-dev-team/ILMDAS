"use client"

import { useEffect, useState, type ReactNode } from "react"
import { useAuth } from "@/context/AuthContext"
import AccessDenied from "@/components/AccessDenied"
import { hasRole, isStaff } from "@/lib/roles"

type RequireRoleProps = {
  children: ReactNode
  role?: string
  requireStaff?: boolean
}

export function RequireRole({ children, role, requireStaff = false }: RequireRoleProps) {
  const { user, loading } = useAuth()
  const [authorized, setAuthorized] = useState<boolean | null>(null)

  useEffect(() => {
    if (loading || !user) {
      setAuthorized(null)
      return
    }
    if (role) {
      setAuthorized(hasRole(user, role))
    } else if (requireStaff) {
      setAuthorized(isStaff(user))
    } else {
      setAuthorized(true)
    }
  }, [loading, user, role, requireStaff])

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
