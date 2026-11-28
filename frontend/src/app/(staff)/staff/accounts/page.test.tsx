import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import StaffAccountsPage from "./page"
import { ApiRequestError } from "@/lib/apiErrors"

jest.mock("@/context/AuthContext", () => ({ useAuth: jest.fn() }))
jest.mock("@/lib/registration", () => ({ createStaffAccount: jest.fn() }))

import { useAuth } from "@/context/AuthContext"
import { createStaffAccount } from "@/lib/registration"

const admin = {
  id: 1,
  username: "admin",
  email: "",
  roles: [{ code: "system_administrator", name: "System Administrator" }],
}

function fill() {
  fireEvent.change(screen.getByLabelText("First name"), { target: { value: "Lensa" } })
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "lensa@example.org" } })
  fireEvent.change(screen.getByLabelText("Username"), { target: { value: "lensa" } })
  fireEvent.click(screen.getByRole("checkbox", { name: "Librarian" }))
}

beforeEach(() => jest.clearAllMocks())

test("an administrator registers a librarian and sees that the invite was sent", async () => {
  ;(useAuth as jest.Mock).mockReturnValue({ user: admin, loading: false })
  ;(createStaffAccount as jest.Mock).mockResolvedValue({
    id: 7,
    username: "lensa",
    email: "lensa@example.org",
    status: "pending",
    roles: [],
  })
  render(<StaffAccountsPage />)
  fill()
  fireEvent.click(screen.getByRole("button", { name: "Create account and send invite" }))

  expect(await screen.findByRole("status")).toHaveTextContent("Invite sent to lensa@example.org.")
  expect(createStaffAccount).toHaveBeenCalledWith({
    username: "lensa",
    email: "lensa@example.org",
    first_name: "Lensa",
    last_name: "",
    roles: ["librarian"],
  })
})

test("only staff roles are offered", () => {
  ;(useAuth as jest.Mock).mockReturnValue({ user: admin, loading: false })
  render(<StaffAccountsPage />)
  expect(screen.queryByRole("checkbox", { name: "Member" })).toBeNull()
  expect(screen.queryByRole("checkbox", { name: "Guest" })).toBeNull()
  expect(screen.getAllByRole("checkbox")).toHaveLength(6)
})

test("a role is required before calling the API", () => {
  ;(useAuth as jest.Mock).mockReturnValue({ user: admin, loading: false })
  render(<StaffAccountsPage />)
  fireEvent.change(screen.getByLabelText("Username"), { target: { value: "x" } })
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "x@example.org" } })
  fireEvent.click(screen.getByRole("button", { name: "Create account and send invite" }))

  expect(screen.getByText("Choose at least one role.")).toBeInTheDocument()
  expect(createStaffAccount).not.toHaveBeenCalled()
})

test("a taken username or email shows the generic message", async () => {
  ;(useAuth as jest.Mock).mockReturnValue({ user: admin, loading: false })
  ;(createStaffAccount as jest.Mock).mockRejectedValue(
    new ApiRequestError("An account cannot be created with these details.", 400)
  )
  render(<StaffAccountsPage />)
  fill()
  fireEvent.click(screen.getByRole("button", { name: "Create account and send invite" }))

  await waitFor(() =>
    expect(screen.getByRole("alert")).toHaveTextContent("cannot be created with these details")
  )
})

test("non-administrators see access denied", () => {
  ;(useAuth as jest.Mock).mockReturnValue({
    user: { ...admin, roles: [{ code: "librarian", name: "Librarian" }] },
    loading: false,
  })
  render(<StaffAccountsPage />)
  expect(screen.getByText("Access Denied")).toBeInTheDocument()
})
