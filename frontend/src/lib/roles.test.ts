import {
  ROLE_SYSTEM_ADMINISTRATOR,
  ROLE_LIBRARIAN,
  ROLE_DIGITAL_ARCHIVIST,
  ROLE_MEMBER,
  hasRole,
  hasAnyRole,
  isSystemAdministrator,
  isStaff,
} from "@/lib/roles"

const adminUser = {
  id: 1,
  username: "admin",
  email: "admin@example.com",
  roles: [{ code: ROLE_SYSTEM_ADMINISTRATOR, name: "System Administrator" }],
}

const librarianUser = {
  id: 2,
  username: "librarian",
  email: "librarian@example.com",
  roles: [{ code: ROLE_LIBRARIAN, name: "Librarian" }],
}

const memberUser = {
  id: 3,
  username: "member",
  email: "member@example.com",
  roles: [{ code: ROLE_MEMBER, name: "Member" }],
}

const multiRoleUser = {
  id: 4,
  username: "multi",
  email: "multi@example.com",
  roles: [
    { code: ROLE_LIBRARIAN, name: "Librarian" },
    { code: ROLE_DIGITAL_ARCHIVIST, name: "Digital Archivist" },
  ],
}

describe("hasRole", () => {
  test("returns true when user has the role", () => {
    expect(hasRole(adminUser, ROLE_SYSTEM_ADMINISTRATOR)).toBe(true)
  })

  test("returns false when user does not have the role", () => {
    expect(hasRole(librarianUser, ROLE_SYSTEM_ADMINISTRATOR)).toBe(false)
  })

  test("returns false for null user", () => {
    expect(hasRole(null, ROLE_SYSTEM_ADMINISTRATOR)).toBe(false)
    expect(hasRole(undefined, ROLE_SYSTEM_ADMINISTRATOR)).toBe(false)
  })
})

describe("hasAnyRole", () => {
  test("returns true when user has any of the roles", () => {
    expect(hasAnyRole(multiRoleUser, [ROLE_LIBRARIAN, ROLE_MEMBER])).toBe(true)
  })

  test("returns false when user has none of the roles", () => {
    expect(hasAnyRole(memberUser, [ROLE_LIBRARIAN, ROLE_SYSTEM_ADMINISTRATOR])).toBe(false)
  })
})

describe("isSystemAdministrator", () => {
  test("returns true for system administrator", () => {
    expect(isSystemAdministrator(adminUser)).toBe(true)
  })

  test("returns false for non-administrator", () => {
    expect(isSystemAdministrator(librarianUser)).toBe(false)
    expect(isSystemAdministrator(memberUser)).toBe(false)
  })

  test("returns false for null user", () => {
    expect(isSystemAdministrator(null)).toBe(false)
  })
})

describe("isStaff", () => {
  test("returns true for staff roles", () => {
    expect(isStaff(adminUser)).toBe(true)
    expect(isStaff(librarianUser)).toBe(true)
  })

  test("returns false for member", () => {
    expect(isStaff(memberUser)).toBe(false)
  })

  test("returns false for null user", () => {
    expect(isStaff(null)).toBe(false)
  })
})
