import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { MembershipPlans } from "@/components/MembershipPlans"
import { ApiRequestError } from "@/lib/apiErrors"
import type { MembershipRequest, MyMembership, Plan } from "@/lib/membership"

jest.mock("@/context/AuthContext", () => ({ useAuth: jest.fn() }))
jest.mock("@/lib/membership", () => ({
  ...jest.requireActual("@/lib/membership"),
  fetchPlans: jest.fn(),
  fetchMyMembership: jest.fn(),
  requestPlan: jest.fn(),
  uploadDocument: jest.fn(),
}))

import { useAuth } from "@/context/AuthContext"
import { fetchMyMembership, fetchPlans, requestPlan, uploadDocument } from "@/lib/membership"

const standard: Plan = {
  id: 1,
  name: "Standard",
  slug: "standard",
  description: "For most readers.",
  price: "250.00",
  currency: "ETB",
  price_display: "ETB 250.00",
  duration_months: 12,
  loan_limit: 3,
  restricted_archive_access: false,
  benefits: "",
  requires_documents: false,
}
const researcher: Plan = {
  ...standard,
  id: 2,
  name: "Researcher",
  slug: "researcher",
  price_display: "ETB 1,250.00",
  duration_months: 6,
  restricted_archive_access: true,
  requires_documents: true,
}

const guest = { id: 5, username: "chaltu", email: "", roles: [{ code: "guest", name: "Guest" }] }
const noMembership: MyMembership = { isMember: false, subscription: null, requests: [] }

function openRequest(plan: Plan): MembershipRequest {
  return {
    id: 9,
    plan,
    status: "awaiting_payment",
    amount: plan.price,
    currency: plan.currency,
    payment_method: "",
    payment_reference: "",
    paid_at: null,
    rejection_reason: "",
    decided_at: null,
    documents: [],
    created_at: "2026-11-28T10:00:00Z",
  }
}

beforeEach(() => {
  jest.clearAllMocks()
  ;(fetchPlans as jest.Mock).mockResolvedValue([standard, researcher])
})

test("visitors see the plans and are asked to sign in", async () => {
  ;(useAuth as jest.Mock).mockReturnValue({ user: null, loading: false })
  render(<MembershipPlans />)

  expect(await screen.findByText("ETB 250.00")).toBeInTheDocument()
  expect(screen.getByText("ETB 1,250.00")).toBeInTheDocument()
  expect(screen.getByText(/for 1 year/)).toBeInTheDocument()
  expect(screen.getByText(/for 6 months/)).toBeInTheDocument()
  expect(screen.getAllByRole("link", { name: "Sign in to request" })[0]).toHaveAttribute(
    "href",
    "/login?next=/membership"
  )
  expect(fetchMyMembership).not.toHaveBeenCalled()
})

test("a guest requests a plan and then sees the request status", async () => {
  ;(useAuth as jest.Mock).mockReturnValue({ user: guest, loading: false })
  ;(fetchMyMembership as jest.Mock)
    .mockResolvedValueOnce(noMembership)
    .mockResolvedValueOnce({ ...noMembership, requests: [openRequest(standard)] })
  ;(requestPlan as jest.Mock).mockResolvedValue(openRequest(standard))
  render(<MembershipPlans />)

  expect(await screen.findByText(/don't have a membership yet/)).toBeInTheDocument()
  fireEvent.click(screen.getAllByRole("button", { name: "Request this plan" })[0])

  expect(await screen.findByText("Awaiting payment")).toBeInTheDocument()
  expect(requestPlan).toHaveBeenCalledWith("standard")
  // One open request at a time: the request buttons are now disabled.
  screen
    .getAllByRole("button", { name: "Request this plan" })
    .forEach((button) => expect(button).toBeDisabled())
})

test("a plan that needs documents offers an upload", async () => {
  ;(useAuth as jest.Mock).mockReturnValue({ user: guest, loading: false })
  ;(fetchMyMembership as jest.Mock).mockResolvedValue({
    ...noMembership,
    requests: [openRequest(researcher)],
  })
  ;(uploadDocument as jest.Mock).mockResolvedValue({ id: 1, original_name: "id.pdf" })
  render(<MembershipPlans />)

  const input = await screen.findByLabelText(/Upload a document/)
  const file = new File(["%PDF-1.4"], "id.pdf", { type: "application/pdf" })
  fireEvent.change(input, { target: { files: [file] } })

  await waitFor(() => expect(uploadDocument).toHaveBeenCalledWith(9, file))
  expect(fetchMyMembership).toHaveBeenCalledTimes(2)
})

test("a current member sees their membership", async () => {
  ;(useAuth as jest.Mock).mockReturnValue({ user: guest, loading: false })
  ;(fetchMyMembership as jest.Mock).mockResolvedValue({
    isMember: true,
    subscription: { id: 1, plan: standard, starts_at: "2026-01-01", ends_at: "2027-01-01" },
    requests: [],
  })
  render(<MembershipPlans />)

  expect(await screen.findByText(/You are a member on the/)).toBeInTheDocument()
})

test("a rejected request shows the reason", async () => {
  ;(useAuth as jest.Mock).mockReturnValue({ user: guest, loading: false })
  ;(fetchMyMembership as jest.Mock).mockResolvedValue({
    ...noMembership,
    requests: [
      { ...openRequest(standard), status: "rejected", rejection_reason: "The ID has expired." },
    ],
  })
  render(<MembershipPlans />)

  expect(await screen.findByText(/The ID has expired\./)).toBeInTheDocument()
})

test("shows the backend's conflict message", async () => {
  ;(useAuth as jest.Mock).mockReturnValue({ user: guest, loading: false })
  ;(fetchMyMembership as jest.Mock).mockResolvedValue(noMembership)
  ;(requestPlan as jest.Mock).mockRejectedValue(
    new ApiRequestError("You already have a membership request in progress.", 409)
  )
  render(<MembershipPlans />)

  fireEvent.click((await screen.findAllByRole("button", { name: "Request this plan" }))[0])
  expect(await screen.findByRole("alert")).toHaveTextContent("already have a membership request")
})
