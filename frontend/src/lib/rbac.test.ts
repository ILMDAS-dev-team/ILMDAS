import { assignRoleToUser, removeRoleFromUser } from "@/lib/rbac"

const ensureCsrfCookie = jest.fn()
const apiFetch = jest.fn()

jest.mock("@/lib/api", () => ({
  ...jest.requireActual("@/lib/api"),
  ensureCsrfCookie: (...args: unknown[]) => ensureCsrfCookie(...args),
  apiFetch: (...args: unknown[]) => apiFetch(...args),
}))

beforeEach(() => {
  ensureCsrfCookie.mockReset().mockResolvedValue("csrf-token")
  apiFetch.mockReset()
})

test("assigning a role sends the CSRF token from the endpoint", async () => {
  apiFetch.mockResolvedValue({ response: { ok: true, status: 201 } })
  await assignRoleToUser(7, "librarian")
  expect(apiFetch).toHaveBeenCalledWith("/api/v1/users/7/roles/", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": "csrf-token" },
    body: JSON.stringify({ role_code: "librarian" }),
  })
})

test("removing a role sends the CSRF token from the endpoint", async () => {
  apiFetch.mockResolvedValue({ response: { ok: true, status: 200 } })
  await removeRoleFromUser(7, "librarian")
  expect(apiFetch).toHaveBeenCalledWith("/api/v1/users/7/roles/librarian/", {
    method: "DELETE",
    headers: { "X-CSRFToken": "csrf-token" },
  })
})

test("a blocked removal surfaces the server's reason", async () => {
  apiFetch.mockResolvedValue({
    response: {
      ok: false,
      status: 409,
      json: async () => ({ errors: ["At least one system administrator must remain."] }),
    },
  })
  await expect(removeRoleFromUser(1, "system_administrator")).rejects.toThrow(
    "At least one system administrator must remain."
  )
})
