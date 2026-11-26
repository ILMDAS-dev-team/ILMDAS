import { render, screen } from "@testing-library/react"
import { LogoutScreen } from "@/components/LogoutScreen"

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

test("ends the session and shows the signed-out confirmation", async () => {
  apiFetch.mockResolvedValue({ response: { ok: true, status: 200 } })

  render(<LogoutScreen />)

  expect(await screen.findByRole("heading", { name: "You have signed out" })).toBeInTheDocument()
  expect(apiFetch).toHaveBeenCalledWith("/api/v1/auth/logout/", {
    method: "POST",
    headers: { "X-CSRFToken": "csrf-token" },
  })
  expect(screen.getByRole("link", { name: "Sign in again" })).toHaveAttribute("href", "/login")
  expect(screen.getByRole("link", { name: "Go to the catalogue" })).toHaveAttribute("href", "/opac")
})

test("still confirms sign-out when no session was left", async () => {
  apiFetch.mockResolvedValue({ response: { ok: false, status: 403 } })

  render(<LogoutScreen />)

  expect(await screen.findByRole("heading", { name: "You have signed out" })).toBeInTheDocument()
})
