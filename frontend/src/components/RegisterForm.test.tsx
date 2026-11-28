import { fireEvent, render, screen } from "@testing-library/react"
import { RegisterForm } from "@/components/RegisterForm"
import { ApiRequestError } from "@/lib/apiErrors"

jest.mock("@/lib/registration", () => ({ registerAccount: jest.fn() }))

import { registerAccount } from "@/lib/registration"

const PASSWORD = "Irreecha-Lib-2026!" // pragma: allowlist secret

function fill() {
  fireEvent.change(screen.getByLabelText("First name"), { target: { value: "Chaltu" } })
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "chaltu@example.org" } })
  fireEvent.change(screen.getByLabelText("Username"), { target: { value: "chaltu" } })
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: PASSWORD } })
  fireEvent.change(screen.getByLabelText("Confirm password"), { target: { value: PASSWORD } })
  fireEvent.click(screen.getByRole("checkbox"))
}

beforeEach(() => jest.clearAllMocks())

test("registers and asks the person to check their email", async () => {
  ;(registerAccount as jest.Mock).mockResolvedValue({ detail: "ok" })
  render(<RegisterForm />)
  fill()
  fireEvent.click(screen.getByRole("button", { name: "Create account" }))

  expect(await screen.findByRole("heading", { name: "Check your email" })).toBeInTheDocument()
  expect(screen.getByRole("status")).toHaveTextContent("chaltu@example.org")
  expect(registerAccount).toHaveBeenCalledWith({
    username: "chaltu",
    email: "chaltu@example.org",
    first_name: "Chaltu",
    last_name: "",
    password: PASSWORD,
    accept_terms: true,
  })
})

test("checks required fields, matching passwords and the terms before calling the API", () => {
  render(<RegisterForm />)
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: PASSWORD } })
  fireEvent.click(screen.getByRole("button", { name: "Create account" }))

  expect(screen.getByText("Choose a username.")).toBeInTheDocument()
  expect(screen.getByText("Enter your email address.")).toBeInTheDocument()
  expect(screen.getByText("The passwords don't match.")).toBeInTheDocument()
  expect(screen.getByText("You must accept the terms to register.")).toBeInTheDocument()
  expect(registerAccount).not.toHaveBeenCalled()
})

test("shows the backend's password message on the password field", async () => {
  ;(registerAccount as jest.Mock).mockRejectedValue(
    new ApiRequestError("Your account could not be created.", 400, {
      password: "This password is too common.", // pragma: allowlist secret
    })
  )
  render(<RegisterForm />)
  fill()
  fireEvent.click(screen.getByRole("button", { name: "Create account" }))

  expect(await screen.findByText("This password is too common.")).toBeInTheDocument()
  expect(screen.getByLabelText("Password")).toHaveAttribute("aria-invalid", "true")
})

test("shows the generic duplicate-account message", async () => {
  ;(registerAccount as jest.Mock).mockRejectedValue(
    new ApiRequestError("An account cannot be created with these details.", 400)
  )
  render(<RegisterForm />)
  fill()
  fireEvent.click(screen.getByRole("button", { name: "Create account" }))

  expect(await screen.findByRole("alert")).toHaveTextContent(
    "An account cannot be created with these details."
  )
})

test("disables the form while the request is in flight", async () => {
  let finish: (value: unknown) => void = () => {}
  ;(registerAccount as jest.Mock).mockReturnValue(new Promise((resolve) => (finish = resolve)))
  render(<RegisterForm />)
  fill()
  fireEvent.click(screen.getByRole("button", { name: "Create account" }))

  expect(screen.getByRole("button", { name: "Creating account…" })).toBeDisabled()
  finish({ detail: "ok" })
  expect(await screen.findByRole("heading", { name: "Check your email" })).toBeInTheDocument()
})
