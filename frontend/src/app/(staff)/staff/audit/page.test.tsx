import { render, screen } from "@testing-library/react"
import AuditPageRoute from "./page"

jest.mock("@/context/AuthContext", () => ({ useAuth: jest.fn() }))
jest.mock("@/lib/audit", () => ({
  ...jest.requireActual("@/lib/audit"),
  fetchAuditEvents: jest.fn(),
}))

import { useAuth } from "@/context/AuthContext"
import { fetchAuditEvents } from "@/lib/audit"

const admin = {
  id: 1,
  username: "admin",
  email: "",
  roles: [{ code: "system_administrator", name: "System Administrator" }],
}
const librarian = { ...admin, roles: [{ code: "librarian", name: "Librarian" }] }

beforeEach(() => {
  jest.clearAllMocks()
  ;(fetchAuditEvents as jest.Mock).mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    results: [
      {
        id: 7,
        timestamp: "2026-11-26T10:00:00Z",
        actor_username: "alice",
        action: "auth.login",
        object_type: "user",
        object_id: "3",
        outcome: "success",
        correlation_id: "cid-123",
        details: {},
      },
    ],
  })
})

test("shows audit events read-only, with no edit or delete actions", async () => {
  ;(useAuth as jest.Mock).mockReturnValue({ user: admin, loading: false })
  render(<AuditPageRoute />)

  expect(await screen.findByText("auth.login")).toBeInTheDocument()
  expect(screen.getByText("cid-123")).toBeInTheDocument()
  expect(screen.queryByRole("button", { name: /edit|delete|remove/i })).toBeNull()
})

test("non-administrators see access denied and nothing is loaded", () => {
  ;(useAuth as jest.Mock).mockReturnValue({ user: librarian, loading: false })
  render(<AuditPageRoute />)

  expect(screen.getByText("Access Denied")).toBeInTheDocument()
  expect(fetchAuditEvents).not.toHaveBeenCalled()
})
