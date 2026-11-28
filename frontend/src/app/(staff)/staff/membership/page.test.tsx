import { fireEvent, render, screen, waitFor, within } from "@testing-library/react"
import MembershipStaffPage from "./page"
import { ApiRequestError } from "@/lib/apiErrors"
import type { ManagedPlan, StaffMembershipRequest } from "@/lib/membership"

jest.mock("@/context/AuthContext", () => ({ useAuth: jest.fn() }))
jest.mock("@/lib/membership", () => ({
  ...jest.requireActual("@/lib/membership"),
  fetchRequestQueue: jest.fn(),
  recordPayment: jest.fn(),
  approveRequest: jest.fn(),
  rejectRequest: jest.fn(),
  fetchManagedPlans: jest.fn(),
  createPlan: jest.fn(),
  updatePlan: jest.fn(),
}))

import { useAuth } from "@/context/AuthContext"
import {
  approveRequest,
  createPlan,
  fetchManagedPlans,
  fetchRequestQueue,
  recordPayment,
  rejectRequest,
  updatePlan,
} from "@/lib/membership"

function user(code: string) {
  return { id: 1, username: code, email: "", roles: [{ code, name: code }] }
}

const plan: ManagedPlan = {
  id: 3,
  name: "Standard",
  slug: "standard",
  description: "",
  price: "250.00",
  currency: "ETB",
  price_display: "ETB 250.00",
  duration_months: 12,
  loan_limit: 3,
  restricted_archive_access: false,
  benefits: "",
  requires_documents: false,
  is_active: true,
  sort_order: 0,
  created_at: "",
  updated_at: "",
}

function request(status: StaffMembershipRequest["status"]): StaffMembershipRequest {
  return {
    id: 11,
    plan,
    status,
    amount: "250.00",
    currency: "ETB",
    payment_method: status === "awaiting_payment" ? "" : "cash",
    payment_reference: status === "awaiting_payment" ? "" : "RCPT-1",
    paid_at: status === "awaiting_payment" ? null : "2026-11-28T10:00:00Z",
    rejection_reason: "",
    decided_at: null,
    documents: [],
    created_at: "2026-11-28T09:00:00Z",
    user: {
      id: 5,
      username: "chaltu",
      email: "chaltu@example.org",
      first_name: "Chaltu",
      last_name: "B",
    },
  }
}

beforeEach(() => {
  jest.clearAllMocks()
  ;(fetchRequestQueue as jest.Mock).mockResolvedValue([request("awaiting_approval")])
  ;(fetchManagedPlans as jest.Mock).mockResolvedValue([plan])
})

test("a librarian approves a paid request, and does not see plan management", async () => {
  ;(useAuth as jest.Mock).mockReturnValue({ user: user("librarian"), loading: false })
  ;(approveRequest as jest.Mock).mockResolvedValue(request("approved"))
  render(<MembershipStaffPage />)

  expect(await screen.findByText(/chaltu@example.org/)).toBeInTheDocument()
  expect(fetchRequestQueue).toHaveBeenCalledWith("awaiting_approval")
  expect(screen.queryByRole("heading", { name: "Membership plans" })).toBeNull()

  fireEvent.click(screen.getByRole("button", { name: "Approve" }))
  await waitFor(() => expect(approveRequest).toHaveBeenCalledWith(11))
  await waitFor(() => expect(fetchRequestQueue).toHaveBeenCalledTimes(2))
})

test("records a payment for a request that is awaiting payment", async () => {
  ;(useAuth as jest.Mock).mockReturnValue({ user: user("librarian"), loading: false })
  ;(fetchRequestQueue as jest.Mock).mockResolvedValue([request("awaiting_payment")])
  ;(recordPayment as jest.Mock).mockResolvedValue(request("awaiting_approval"))
  render(<MembershipStaffPage />)

  fireEvent.change(await screen.findByLabelText("Status"), {
    target: { value: "awaiting_payment" },
  })
  const form = await screen.findByRole("form", { name: "Record payment for chaltu" })
  fireEvent.change(within(form).getByLabelText("Method"), { target: { value: "telebirr" } })
  fireEvent.change(within(form).getByLabelText("Reference"), { target: { value: "TB-77" } })
  fireEvent.click(within(form).getByRole("button", { name: "Record payment" }))

  await waitFor(() => expect(recordPayment).toHaveBeenCalledWith(11, "telebirr", "TB-77"))
})

test("rejection needs a reason, and backend errors are shown", async () => {
  ;(useAuth as jest.Mock).mockReturnValue({ user: user("manager"), loading: false })
  ;(rejectRequest as jest.Mock).mockRejectedValue(
    new ApiRequestError("This request has already been decided.", 409)
  )
  render(<MembershipStaffPage />)

  const form = await screen.findByRole("form", { name: "Reject request from chaltu" })
  fireEvent.click(within(form).getByRole("button", { name: "Reject" }))
  expect(screen.getByRole("alert")).toHaveTextContent("Give a reason")
  expect(rejectRequest).not.toHaveBeenCalled()

  fireEvent.change(within(form).getByLabelText("Reason"), { target: { value: "Expired ID" } })
  fireEvent.click(within(form).getByRole("button", { name: "Reject" }))
  expect(await screen.findByText("This request has already been decided.")).toBeInTheDocument()
  expect(rejectRequest).toHaveBeenCalledWith(11, "Expired ID")
})

test("a manager creates and retires plans", async () => {
  ;(useAuth as jest.Mock).mockReturnValue({ user: user("manager"), loading: false })
  ;(createPlan as jest.Mock).mockResolvedValue(plan)
  ;(updatePlan as jest.Mock).mockResolvedValue({ ...plan, is_active: false })
  render(<MembershipStaffPage />)

  expect(await screen.findByRole("heading", { name: "Membership plans" })).toBeInTheDocument()
  const form = screen.getByRole("form", { name: "New plan" })
  fireEvent.change(within(form).getByLabelText("Name"), { target: { value: "Student" } })
  fireEvent.change(within(form).getByLabelText("Slug"), { target: { value: "student" } })
  fireEvent.change(within(form).getByLabelText("Price"), { target: { value: "100.00" } })
  fireEvent.click(within(form).getByRole("button", { name: "Save plan" }))
  await waitFor(() =>
    expect(createPlan).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "Student",
        slug: "student",
        price: "100.00",
        duration_months: 12,
      })
    )
  )

  fireEvent.click(await screen.findByRole("button", { name: "Retire" }))
  await waitFor(() => expect(updatePlan).toHaveBeenCalledWith(3, { is_active: false }))
})

test("a plan field error from the backend is shown on the field", async () => {
  ;(useAuth as jest.Mock).mockReturnValue({ user: user("system_administrator"), loading: false })
  ;(createPlan as jest.Mock).mockRejectedValue(
    new ApiRequestError("The plan could not be saved.", 400, {
      slug: "membership plan with this slug already exists.",
    })
  )
  render(<MembershipStaffPage />)

  const form = await screen.findByRole("form", { name: "New plan" })
  fireEvent.click(within(form).getByRole("button", { name: "Save plan" }))
  expect(await within(form).findByText(/slug already exists/)).toBeInTheDocument()
})

test("roles without approval rights see access denied and nothing is loaded", () => {
  ;(useAuth as jest.Mock).mockReturnValue({ user: user("journal_editor"), loading: false })
  render(<MembershipStaffPage />)

  expect(screen.getByText("Access Denied")).toBeInTheDocument()
  expect(fetchRequestQueue).not.toHaveBeenCalled()
})
