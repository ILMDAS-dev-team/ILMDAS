/**
 * Membership plans, requests and the staff approval queue (ILMDAS-553, ILMDAS-554).
 */

import { apiFetch, csrfHeader, ensureCsrfCookie } from "@/lib/api"
import { getJson, readApiError, sendJson } from "@/lib/apiErrors"

export type Plan = {
  id: number
  name: string
  slug: string
  description: string
  price: string
  currency: "ETB" | "USD"
  price_display: string
  duration_months: number
  loan_limit: number
  restricted_archive_access: boolean
  benefits: string
  requires_documents: boolean
}

export type ManagedPlan = Plan & {
  is_active: boolean
  sort_order: number
  created_at: string
  updated_at: string
}

export type PlanInput = Partial<
  Pick<
    ManagedPlan,
    | "name"
    | "slug"
    | "description"
    | "price"
    | "currency"
    | "duration_months"
    | "loan_limit"
    | "restricted_archive_access"
    | "benefits"
    | "requires_documents"
    | "is_active"
    | "sort_order"
  >
>

export type RequestStatus = "awaiting_payment" | "awaiting_approval" | "approved" | "rejected"

export const REQUEST_STATUS_LABELS: Record<RequestStatus, string> = {
  awaiting_payment: "Awaiting payment",
  awaiting_approval: "Awaiting approval",
  approved: "Approved",
  rejected: "Rejected",
}

export const PAYMENT_METHODS: { value: string; label: string }[] = [
  { value: "cash", label: "Cash" },
  { value: "bank_transfer", label: "Bank transfer" },
  { value: "telebirr", label: "Telebirr" },
  { value: "cbe_birr", label: "CBE Birr" },
  { value: "card", label: "VISA / Mastercard" },
  { value: "other", label: "Other" },
]

export type MembershipDocument = {
  id: number
  original_name: string
  content_type: string
  size: number
  uploaded_at: string
}

export type MembershipRequest = {
  id: number
  plan: Plan
  status: RequestStatus
  amount: string
  currency: string
  payment_method: string
  payment_reference: string
  paid_at: string | null
  rejection_reason: string
  decided_at: string | null
  documents: MembershipDocument[]
  created_at: string
}

export type StaffMembershipRequest = MembershipRequest & {
  user: { id: number; username: string; email: string; first_name: string; last_name: string }
}

export type Subscription = {
  id: number
  plan: Plan
  starts_at: string
  ends_at: string
}

export type MyMembership = {
  isMember: boolean
  subscription: Subscription | null
  requests: MembershipRequest[]
}

export function isOpenRequest(request: MembershipRequest): boolean {
  return request.status === "awaiting_payment" || request.status === "awaiting_approval"
}

// ---- Guests and members ----

export function fetchPlans(): Promise<Plan[]> {
  return getJson("/api/v1/membership/plans/", "Could not load membership plans.")
}

export function fetchMyMembership(): Promise<MyMembership> {
  return getJson("/api/v1/membership/me/", "Could not load your membership.")
}

export function requestPlan(slug: string): Promise<MembershipRequest> {
  return sendJson("/api/v1/membership/requests/", { plan: slug }, "Could not request this plan.")
}

/** Upload a supporting document. Multipart, so the browser sets the Content-Type. */
export async function uploadDocument(requestId: number, file: File): Promise<MembershipDocument> {
  const csrfToken = await ensureCsrfCookie()
  const form = new FormData()
  form.append("file", file)
  const { response } = await apiFetch(`/api/v1/membership/requests/${requestId}/documents/`, {
    method: "POST",
    headers: csrfHeader(csrfToken),
    body: form,
  })
  if (!response.ok) {
    throw await readApiError(response, "The document could not be uploaded.")
  }
  return (await response.json()) as MembershipDocument
}

// ---- Staff approval queue ----

export function fetchRequestQueue(status: RequestStatus): Promise<StaffMembershipRequest[]> {
  const query = new URLSearchParams({ status })
  return getJson(`/api/v1/membership/manage/requests/?${query}`, "Could not load requests.")
}

export function recordPayment(
  requestId: number,
  method: string,
  reference: string
): Promise<StaffMembershipRequest> {
  return sendJson(
    `/api/v1/membership/manage/requests/${requestId}/payment/`,
    { method, reference },
    "The payment could not be recorded."
  )
}

export function approveRequest(requestId: number): Promise<StaffMembershipRequest> {
  return sendJson(
    `/api/v1/membership/manage/requests/${requestId}/approve/`,
    undefined,
    "The request could not be approved."
  )
}

export function rejectRequest(requestId: number, reason: string): Promise<StaffMembershipRequest> {
  return sendJson(
    `/api/v1/membership/manage/requests/${requestId}/reject/`,
    { reason },
    "The request could not be rejected."
  )
}

// ---- Plan management (managers and administrators) ----

export function fetchManagedPlans(): Promise<ManagedPlan[]> {
  return getJson("/api/v1/membership/manage/plans/", "Could not load plans.")
}

export function createPlan(input: PlanInput): Promise<ManagedPlan> {
  return sendJson("/api/v1/membership/manage/plans/", input, "The plan could not be saved.")
}

export function updatePlan(id: number, input: PlanInput): Promise<ManagedPlan> {
  return sendJson(
    `/api/v1/membership/manage/plans/${id}/`,
    input,
    "The plan could not be saved.",
    "PATCH"
  )
}
