"use client"

import { useEffect, useState, type ReactNode } from "react"
import { useAuth } from "@/context/AuthContext"
import { fetchRoles, fetchUsers, assignRoleToUser, removeRoleFromUser } from "@/lib/rbac"
import type { UserSummary } from "@/lib/rbac"
import { ALL_ROLE_CODES, ROLE_NAMES, ROLE_SYSTEM_ADMINISTRATOR } from "@/lib/roles"

type RoleAssignmentProps = { children?: ReactNode }

export default function RoleAssignmentPage({ children }: RoleAssignmentProps) {
  const { isSystemAdministrator, loading } = useAuth()
  const [users, setUsers] = useState<UserSummary[]>([])
  const [loadingData, setLoadingData] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [assigningUserId, setAssigningUserId] = useState<number | null>(null)
  const [selectedRole, setSelectedRole] = useState<string | null>(null)

  useEffect(() => {
    if (!isSystemAdministrator()) {
      return
    }
    Promise.all([fetchRoles(), fetchUsers()])
      .then(([, u]) => {
        setUsers(u)
      })
      .catch(() => setError("Failed to load roles and users."))
      .finally(() => setLoadingData(false))
  }, [isSystemAdministrator])

  if (!isSystemAdministrator()) {
    return (
      <section>
        <h1>Access Denied</h1>
        <p>Only System Administrators can access role management.</p>
      </section>
    )
  }

  if (loading || loadingData) {
    return (
      <section>
        <p>Loading role management...</p>
      </section>
    )
  }

  const handleAssign = async () => {
    if (!assigningUserId || !selectedRole) return
    setError(null)
    setSuccess(null)
    try {
      await assignRoleToUser(assigningUserId, selectedRole)
      setSuccess(`Role "${ROLE_NAMES[selectedRole] ?? selectedRole}" assigned.`)
      const updated = await fetchUsers()
      setUsers(updated)
      setAssigningUserId(null)
      setSelectedRole(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to assign role.")
    }
  }

  const handleRemove = async (userId: number, roleCode: string) => {
    setError(null)
    setSuccess(null)
    try {
      await removeRoleFromUser(userId, roleCode)
      setSuccess("Role removed.")
      const updated = await fetchUsers()
      setUsers(updated)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove role.")
    }
  }

  return (
    <section>
      <h1>Role Management</h1>
      <p>Assign roles to users. Only System Administrators can manage roles.</p>

      {error && <p style={{ color: "red" }}>{error}</p>}
      {success && <p style={{ color: "green" }}>{success}</p>}

      <h2>Assign Role</h2>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          handleAssign()
        }}
      >
        <label>
          User:
          <select
            disabled={!assigningUserId}
            onChange={(e) => setAssigningUserId(Number(e.target.value))}
            value={assigningUserId || ""}
          >
            <option value="">Select a user</option>
            {users.map((u: UserSummary) => (
              <option key={u.id} value={u.id}>
                {u.username} (
                {u.roles.map((r: { code: string; name: string }) => r.code).join(", ") ||
                  "no roles"}
                )
              </option>
            ))}
          </select>
        </label>
        <label>
          Role:
          <select
            disabled={!assigningUserId || !selectedRole}
            onChange={(e) => setSelectedRole(e.target.value)}
            value={selectedRole || ""}
          >
            <option value="">Select a role</option>
            {ALL_ROLE_CODES.map((code) => (
              <option key={code} value={code}>
                {ROLE_NAMES[code] ?? code}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" disabled={!assigningUserId || !selectedRole}>
          Assign Role
        </button>
      </form>

      <h2>Current Users</h2>
      <ul>
        {users.map((u: UserSummary) => (
          <li key={u.id}>
            <strong>{u.username}</strong>
            <ul>
              {u.roles.map((r: { code: string; name: string }) => (
                <li key={r.code}>
                  {ROLE_NAMES[r.code] ?? r.code}{" "}
                  <button
                    type="button"
                    onClick={() => handleRemove(u.id, r.code)}
                    disabled={r.code === ROLE_SYSTEM_ADMINISTRATOR && u.roles.length === 1}
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>

      {children}
    </section>
  )
}
