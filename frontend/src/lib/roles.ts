/**
 * Role code identifiers and RBAC helpers for the ILMDAS frontend.
 */

export const ROLE_SYSTEM_ADMINISTRATOR = "system_administrator"
export const ROLE_LIBRARIAN = "librarian"
export const ROLE_DIGITAL_ARCHIVIST = "digital_archivist"
export const ROLE_JOURNAL_EDITOR = "journal_editor"
export const ROLE_MEMBER = "member"
export const ROLE_MANAGER = "manager"
export const ROLE_INTEGRATION_ADMINISTRATOR = "integration_administrator"

export const ALL_ROLE_CODES = [
  ROLE_SYSTEM_ADMINISTRATOR,
  ROLE_LIBRARIAN,
  ROLE_DIGITAL_ARCHIVIST,
  ROLE_JOURNAL_EDITOR,
  ROLE_MEMBER,
  ROLE_MANAGER,
  ROLE_INTEGRATION_ADMINISTRATOR,
]

export const ROLE_NAMES: Record<string, string> = {
  [ROLE_SYSTEM_ADMINISTRATOR]: "System Administrator",
  [ROLE_LIBRARIAN]: "Librarian",
  [ROLE_DIGITAL_ARCHIVIST]: "Digital Archivist",
  [ROLE_JOURNAL_EDITOR]: "Journal Editor",
  [ROLE_MEMBER]: "Member",
  [ROLE_MANAGER]: "Manager",
  [ROLE_INTEGRATION_ADMINISTRATOR]: "Integration Administrator",
}

export type UserRole = {
  code: string
  name: string
}

export type AuthUser = {
  id: number
  username: string
  email: string
  roles: UserRole[]
}

export function hasRole(user: AuthUser | null | undefined, roleCode: string): boolean {
  if (!user) return false
  return user.roles.some((r) => r.code === roleCode)
}

export function hasAnyRole(user: AuthUser | null | undefined, roleCodes: string[]): boolean {
  if (!user) return false
  return user.roles.some((r) => roleCodes.includes(r.code))
}

export function isSystemAdministrator(user: AuthUser | null | undefined): boolean {
  return hasRole(user, ROLE_SYSTEM_ADMINISTRATOR)
}

export function isStaff(user: AuthUser | null | undefined): boolean {
  if (!user) return false
  const staffRoles = [
    ROLE_SYSTEM_ADMINISTRATOR,
    ROLE_LIBRARIAN,
    ROLE_DIGITAL_ARCHIVIST,
    ROLE_JOURNAL_EDITOR,
    ROLE_MANAGER,
    ROLE_INTEGRATION_ADMINISTRATOR,
  ]
  return user.roles.some((r) => staffRoles.includes(r.code))
}
