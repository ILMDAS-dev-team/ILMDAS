import { fireEvent, render, screen } from "@testing-library/react"
import { AcceptInviteForm } from "@/components/AcceptInviteForm"
import { ApiRequestError } from "@/lib/apiErrors"

jest.mock("@/lib/registration", () => ({ acceptInvite: jest.fn() }))

import { acceptInvite } from "@/lib/registration"

const PASSWORD = "Gadaa-Archive-2026!" // pragma: allowlist secret

function fill(password: string, confirm: string) {
  fireEvent.change(screen.getByLabelText("New password"), { target: { value: password } })
  fireEvent.change(screen.getByLabelText("Confirm password"), { target: { value: confirm } })
}

beforeEach(() => jest.clearAllMocks())

test("sets the password and offers staff sign-in", async () => {
  ;(acceptInvite as jest.Mock).mockResolvedValue({ detail: "ok" })
  render(<AcceptInviteForm uid="Mg" token="tok" />)
  fill(PASSWORD, PASSWORD)
  fireEvent.click(screen.getByRole("button", { name: "Set password" }))

  expect(await screen.findByRole("heading", { name: "Your password is set" })).toBeInTheDocument()
  expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute(
    "href",
    "/login?next=/staff"
  )
  expect(acceptInvite).toHaveBeenCalledWith("Mg", "tok", PASSWORD)
})

test("passwords must match", () => {
  render(<AcceptInviteForm uid="Mg" token="tok" />)
  fill(PASSWORD, "different")
  fireEvent.click(screen.getByRole("button", { name: "Set password" }))
  expect(screen.getByText("The passwords don't match.")).toBeInTheDocument()
  expect(acceptInvite).not.toHaveBeenCalled()
})

test("a used or expired invite shows the link error", async () => {
  ;(acceptInvite as jest.Mock).mockRejectedValue(
    new ApiRequestError("Your password could not be set.", 400, {
      token: "This link is invalid or has expired.",
    })
  )
  render(<AcceptInviteForm uid="Mg" token="used" />)
  fill(PASSWORD, PASSWORD)
  fireEvent.click(screen.getByRole("button", { name: "Set password" }))

  expect(await screen.findByRole("alert")).toHaveTextContent("This link is invalid or has expired.")
})

test("a weak password shows the backend's message on the field", async () => {
  ;(acceptInvite as jest.Mock).mockRejectedValue(
    new ApiRequestError("Your password could not be set.", 400, {
      password: "This password is too short.", // pragma: allowlist secret
    })
  )
  render(<AcceptInviteForm uid="Mg" token="tok" />)
  fill("short", "short")
  fireEvent.click(screen.getByRole("button", { name: "Set password" }))

  expect(await screen.findByText("This password is too short.")).toBeInTheDocument()
  expect(screen.queryByRole("alert")).toBeNull()
})
