/**
 * Backend API calls for RBAC (roles and user-role assignment).
 */

import { apiFetch } from "@/lib/api"
import type { AuthUser, UserRole } from "@/lib/roles"

export type Role = {
  id: number
  name: string
  code: string
  description: string
  created_at: string
}

export type UserSummary = {
  id: number
  username: string
  email: string
  roles: UserRole[]
}

type AssignRoleBody = {
  role_code: string
}

export async function fetchRoles(): Promise<Role[]> {
  const { response } = await apiFetch("/api/v1/roles/")
  if (!response.ok) throw new Error(`Failed to fetch roles: ${response.status}`)
  return (await response.json()) as Role[]
}

export async function fetchUsers(): Promise<UserSummary[]> {
  const { response } = await apiFetch("/api/v1/users/")
  if (!response.ok) throw new Error(`Failed to fetch users: ${response.status}`)
  return (await response.json()) as UserSummary[]
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  const { response } = await apiFetch("/api/v1/auth/session/")
  if (!response.ok) throw new Error(`Failed to fetch session: ${response.status}`)
  const body = (await response.json()) as { authenticated: boolean; user: AuthUser }
  return body.user
}

export async function assignRoleToUser(userId: number, roleCode: string): Promise<void> {
  const { response } = await apiFetch(`/api/v1/users/${userId}/roles/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role_code: roleCode } as AssignRoleBody),
  })
  if (!response.ok) {
    if (response.status === 409) {
      const body = (await response.json()) as { detail: string }
      throw new Error(body.detail || "Role already assigned")
    }
    throw new Error(`Failed to assign role: ${response.status}`)
  }
}

export async function removeRoleFromUser(userId: number, roleCode: string): Promise<void> {
  const { response } = await apiFetch(`/api/v1/users/${userId}/roles/${roleCode}/`, {
    method: "DELETE",
  })
  if (!response.ok && response.status !== 404) {
    throw new Error(`Failed to remove role: ${response.status}`)
  }
}
