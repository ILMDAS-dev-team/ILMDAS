import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { LoginForm } from "@/components/LoginForm"

const ensureCsrfCookie = jest.fn()
const apiFetch = jest.fn()

jest.mock("@/lib/api", () => ({
  ensureCsrfCookie: (...args: unknown[]) => ensureCsrfCookie(...args),
  apiFetch: (...args: unknown[]) => apiFetch(...args),
}))

beforeEach(() => {
  ensureCsrfCookie.mockReset()
  apiFetch.mockReset()
  ensureCsrfCookie.mockResolvedValue("csrf-token")
})

test("shows a generic error when sign-in fails", async () => {
  apiFetch.mockResolvedValue({
    response: { ok: false, status: 401 },
  })

  render(<LoginForm title="Staff sign in" redirectTo="/staff" />)
  fireEvent.change(screen.getByLabelText("Username"), { target: { value: "someone" } })
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "secret" } })
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }))

  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Sign-in failed. Check your details and try again."
  )
  expect(screen.queryByText(/username exists/i)).toBeNull()
})

test("shows loading state while signing in", async () => {
  let resolveFetch: (value: unknown) => void = () => undefined
  apiFetch.mockReturnValue(
    new Promise((resolve) => {
      resolveFetch = resolve
    })
  )

  render(<LoginForm title="Public sign in" redirectTo="/" />)
  fireEvent.change(screen.getByLabelText("Username"), { target: { value: "someone" } })
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "secret" } })
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }))

  expect(screen.getByRole("button", { name: "Signing in…" })).toBeDisabled()

  resolveFetch({ response: { ok: false, status: 401 } })
  await waitFor(() => {
    expect(screen.getByRole("button", { name: "Sign in" })).toBeEnabled()
  })
})
