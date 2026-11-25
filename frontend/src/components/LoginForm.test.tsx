import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { LoginForm } from "@/components/LoginForm"

const ensureCsrfCookie = jest.fn()
const apiFetch = jest.fn()

const navigateTo = jest.fn()

jest.mock("@/lib/api", () => ({
  ...jest.requireActual("@/lib/api"),
  ensureCsrfCookie: (...args: unknown[]) => ensureCsrfCookie(...args),
  apiFetch: (...args: unknown[]) => apiFetch(...args),
}))

jest.mock("@/lib/navigation", () => ({
  navigateTo: (...args: unknown[]) => navigateTo(...args),
}))

beforeEach(() => {
  ensureCsrfCookie.mockReset()
  apiFetch.mockReset()
  navigateTo.mockReset()
  ensureCsrfCookie.mockResolvedValue("csrf-token")
})

test("signs in with the CSRF token and goes to the redirect target", async () => {
  apiFetch.mockResolvedValue({ response: { ok: true, status: 200 } })

  render(<LoginForm title="Sign in" redirectTo="/staff" />)
  fireEvent.change(screen.getByLabelText("Email or member ID"), {
    target: { value: "  someone  " },
  })
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "secret" } })
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }))

  await waitFor(() => expect(navigateTo).toHaveBeenCalledWith("/staff"))
  expect(apiFetch).toHaveBeenCalledWith("/api/v1/auth/login/", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": "csrf-token" },
    body: JSON.stringify({ username: "someone", password: "secret" }),
  })
  expect(screen.queryByRole("alert")).toBeNull()
})

test("shows a generic error when sign-in fails", async () => {
  apiFetch.mockResolvedValue({
    response: { ok: false, status: 401 },
  })

  render(<LoginForm title="Staff sign in" redirectTo="/staff" />)
  fireEvent.change(screen.getByLabelText("Email or member ID"), { target: { value: "someone" } })
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "secret" } })
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }))

  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Email or password is not correct. Try again."
  )
  expect(screen.queryByText(/username exists/i)).toBeNull()
  expect(navigateTo).not.toHaveBeenCalled()
})

test("shows loading state while signing in", async () => {
  let resolveFetch: (value: unknown) => void = () => undefined
  apiFetch.mockReturnValue(
    new Promise((resolve) => {
      resolveFetch = resolve
    })
  )

  render(<LoginForm title="Public sign in" redirectTo="/" />)
  fireEvent.change(screen.getByLabelText("Email or member ID"), { target: { value: "someone" } })
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "secret" } })
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }))

  expect(screen.getByRole("button", { name: "Signing in…" })).toBeDisabled()

  resolveFetch({ response: { ok: false, status: 401 } })
  await waitFor(() => {
    expect(screen.getByRole("button", { name: "Sign in" })).toBeEnabled()
  })
})

test("shows field errors and does not call the API when fields are empty", async () => {
  render(<LoginForm title="Sign in" redirectTo="/" />)
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }))

  expect(await screen.findByText("Enter your email or member ID.")).toBeInTheDocument()
  expect(screen.getByText("Enter your password.")).toBeInTheDocument()
  expect(screen.getByLabelText("Email or member ID")).toHaveAttribute("aria-invalid", "true")
  expect(apiFetch).not.toHaveBeenCalled()
})
