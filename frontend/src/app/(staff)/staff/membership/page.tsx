"use client"

import { FormEvent, useCallback, useEffect, useState } from "react"
import { RequireRole } from "@/components/RequireRole"
import { useAuth } from "@/context/AuthContext"
import { errorFields, errorMessage, type FieldErrors } from "@/lib/apiErrors"
import {
  approveRequest,
  createPlan,
  fetchManagedPlans,
  fetchRequestQueue,
  PAYMENT_METHODS,
  recordPayment,
  rejectRequest,
  REQUEST_STATUS_LABELS,
  updatePlan,
  type ManagedPlan,
  type PlanInput,
  type RequestStatus,
  type StaffMembershipRequest,
} from "@/lib/membership"
import { hasAnyRole, ROLE_LIBRARIAN, ROLE_MANAGER, ROLE_SYSTEM_ADMINISTRATOR } from "@/lib/roles"

const APPROVER_ROLES = [ROLE_LIBRARIAN, ROLE_MANAGER, ROLE_SYSTEM_ADMINISTRATOR]
const PLAN_MANAGER_ROLES = [ROLE_MANAGER, ROLE_SYSTEM_ADMINISTRATOR]
const STATUSES = Object.keys(REQUEST_STATUS_LABELS) as RequestStatus[]

// ---- Approval queue (ILMDAS-554) ----

function RequestActions({
  request,
  onDone,
}: {
  request: StaffMembershipRequest
  onDone: () => Promise<void>
}) {
  const [method, setMethod] = useState(PAYMENT_METHODS[0].value)
  const [reference, setReference] = useState("")
  const [reason, setReason] = useState("")
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run(action: () => Promise<unknown>) {
    setBusy(true)
    setError(null)
    try {
      await action()
      await onDone()
    } catch (caught) {
      setError(errorMessage(caught, "The action could not be completed."))
    } finally {
      setBusy(false)
    }
  }

  function onPayment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!reference.trim()) {
      setError("Enter the receipt or transaction reference.")
      return
    }
    void run(() => recordPayment(request.id, method, reference.trim()))
  }

  function onReject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!reason.trim()) {
      setError("Give a reason for the rejection.")
      return
    }
    void run(() => rejectRequest(request.id, reason.trim()))
  }

  const name = request.user.username
  const open = request.status === "awaiting_payment" || request.status === "awaiting_approval"

  return (
    <div>
      {request.status === "awaiting_payment" ? (
        <form onSubmit={onPayment} aria-label={`Record payment for ${name}`}>
          <label>
            Method
            <select
              value={method}
              onChange={(event) => setMethod(event.target.value)}
              disabled={busy}
            >
              {PAYMENT_METHODS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Reference
            <input
              value={reference}
              onChange={(event) => setReference(event.target.value)}
              disabled={busy}
            />
          </label>
          <button type="submit" disabled={busy}>
            Record payment
          </button>
        </form>
      ) : null}
      {request.status === "awaiting_approval" ? (
        <button
          type="button"
          disabled={busy}
          onClick={() => void run(() => approveRequest(request.id))}
        >
          Approve
        </button>
      ) : null}
      {open ? (
        <form onSubmit={onReject} aria-label={`Reject request from ${name}`}>
          <label>
            Reason
            <input
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              disabled={busy}
            />
          </label>
          <button type="submit" disabled={busy}>
            Reject
          </button>
        </form>
      ) : null}
      {request.status === "rejected" ? <span>{request.rejection_reason}</span> : null}
      {error ? <p role="alert">{error}</p> : null}
    </div>
  )
}

function RequestQueue() {
  const [status, setStatus] = useState<RequestStatus>("awaiting_approval")
  const [requests, setRequests] = useState<StaffMembershipRequest[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async (current: RequestStatus) => {
    setLoading(true)
    setError(null)
    try {
      setRequests(await fetchRequestQueue(current))
    } catch (caught) {
      setError(errorMessage(caught, "Could not load membership requests."))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load(status)
  }, [status, load])

  return (
    <section aria-labelledby="queue-heading">
      <h2 id="queue-heading">Membership requests</h2>
      <label>
        Status
        <select value={status} onChange={(event) => setStatus(event.target.value as RequestStatus)}>
          {STATUSES.map((value) => (
            <option key={value} value={value}>
              {REQUEST_STATUS_LABELS[value]}
            </option>
          ))}
        </select>
      </label>

      {error ? <p role="alert">{error}</p> : null}
      {loading ? <p>Loading...</p> : null}
      {requests && !loading && requests.length === 0 ? <p>No requests with this status.</p> : null}
      {requests && !loading && requests.length > 0 ? (
        <table>
          <thead>
            <tr>
              <th scope="col">Applicant</th>
              <th scope="col">Plan</th>
              <th scope="col">Amount</th>
              <th scope="col">Payment</th>
              <th scope="col">Documents</th>
              <th scope="col">Requested</th>
              <th scope="col">Actions</th>
            </tr>
          </thead>
          <tbody>
            {requests.map((request) => (
              <tr key={request.id}>
                <td>
                  {request.user.first_name} {request.user.last_name} ({request.user.username})
                  <br />
                  {request.user.email}
                </td>
                <td>{request.plan.name}</td>
                <td>
                  {request.currency} {request.amount}
                </td>
                <td>
                  {request.paid_at
                    ? `${request.payment_method}: ${request.payment_reference}`
                    : "Not paid"}
                </td>
                <td>
                  {request.documents.length > 0
                    ? request.documents.map((document) => document.original_name).join(", ")
                    : request.plan.requires_documents
                      ? "Required, none uploaded"
                      : "Not needed"}
                </td>
                <td>{new Date(request.created_at).toLocaleDateString()}</td>
                <td>
                  <RequestActions request={request} onDone={() => load(status)} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </section>
  )
}

// ---- Plan management (ILMDAS-553) ----

type PlanDraft = {
  name: string
  slug: string
  price: string
  currency: "ETB" | "USD"
  duration_months: string
  loan_limit: string
  requires_documents: boolean
  restricted_archive_access: boolean
  description: string
  benefits: string
}

const EMPTY_DRAFT: PlanDraft = {
  name: "",
  slug: "",
  price: "",
  currency: "ETB",
  duration_months: "12",
  loan_limit: "0",
  requires_documents: false,
  restricted_archive_access: false,
  description: "",
  benefits: "",
}

function toDraft(plan: ManagedPlan): PlanDraft {
  return {
    name: plan.name,
    slug: plan.slug,
    price: plan.price,
    currency: plan.currency,
    duration_months: String(plan.duration_months),
    loan_limit: String(plan.loan_limit),
    requires_documents: plan.requires_documents,
    restricted_archive_access: plan.restricted_archive_access,
    description: plan.description,
    benefits: plan.benefits,
  }
}

function toInput(draft: PlanDraft): PlanInput {
  return {
    ...draft,
    duration_months: Number(draft.duration_months),
    loan_limit: Number(draft.loan_limit),
  }
}

function PlanManager() {
  const [plans, setPlans] = useState<ManagedPlan[] | null>(null)
  const [draft, setDraft] = useState<PlanDraft>(EMPTY_DRAFT)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    try {
      setPlans(await fetchManagedPlans())
    } catch (caught) {
      setError(errorMessage(caught, "Could not load plans."))
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  function set<K extends keyof PlanDraft>(key: K, value: PlanDraft[K]) {
    setDraft((current) => ({ ...current, [key]: value }))
  }

  function startEdit(plan: ManagedPlan) {
    setEditingId(plan.id)
    setDraft(toDraft(plan))
    setFieldErrors({})
    setError(null)
  }

  function reset() {
    setEditingId(null)
    setDraft(EMPTY_DRAFT)
    setFieldErrors({})
  }

  async function onSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setError(null)
    setFieldErrors({})
    try {
      if (editingId === null) {
        await createPlan(toInput(draft))
      } else {
        await updatePlan(editingId, toInput(draft))
      }
      reset()
      await load()
    } catch (caught) {
      setFieldErrors(errorFields(caught))
      setError(errorMessage(caught, "The plan could not be saved."))
    } finally {
      setSaving(false)
    }
  }

  async function toggleActive(plan: ManagedPlan) {
    setError(null)
    try {
      await updatePlan(plan.id, { is_active: !plan.is_active })
      await load()
    } catch (caught) {
      setError(errorMessage(caught, "The plan could not be updated."))
    }
  }

  function input(key: "name" | "slug" | "price" | "duration_months" | "loan_limit", label: string) {
    return (
      <label>
        {label}
        <input
          value={draft[key]}
          onChange={(event) => set(key, event.target.value)}
          disabled={saving}
          aria-invalid={fieldErrors[key] ? true : undefined}
        />
        {fieldErrors[key] ? <span role="alert">{fieldErrors[key]}</span> : null}
      </label>
    )
  }

  return (
    <section aria-labelledby="plans-heading">
      <h2 id="plans-heading">Membership plans</h2>
      {error ? <p role="alert">{error}</p> : null}
      {plans === null && !error ? <p>Loading...</p> : null}
      {plans && plans.length > 0 ? (
        <table>
          <thead>
            <tr>
              <th scope="col">Plan</th>
              <th scope="col">Price</th>
              <th scope="col">Duration</th>
              <th scope="col">Documents</th>
              <th scope="col">Status</th>
              <th scope="col">Actions</th>
            </tr>
          </thead>
          <tbody>
            {plans.map((plan) => (
              <tr key={plan.id}>
                <td>{plan.name}</td>
                <td>{plan.price_display}</td>
                <td>{plan.duration_months} months</td>
                <td>{plan.requires_documents ? "Required" : "Not needed"}</td>
                <td>{plan.is_active ? "Active" : "Retired"}</td>
                <td>
                  <button type="button" onClick={() => startEdit(plan)}>
                    Edit
                  </button>{" "}
                  <button type="button" onClick={() => void toggleActive(plan)}>
                    {plan.is_active ? "Retire" : "Reactivate"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}

      <form onSubmit={onSave} aria-label={editingId === null ? "New plan" : "Edit plan"}>
        <h3>{editingId === null ? "New plan" : `Edit ${draft.name}`}</h3>
        {input("name", "Name")}
        {input("slug", "Slug")}
        {input("price", "Price")}
        <label>
          Currency
          <select
            value={draft.currency}
            onChange={(event) => set("currency", event.target.value as "ETB" | "USD")}
            disabled={saving}
          >
            <option value="ETB">ETB</option>
            <option value="USD">USD</option>
          </select>
        </label>
        {input("duration_months", "Duration (months)")}
        {input("loan_limit", "Loan limit")}
        <label>
          <input
            type="checkbox"
            checked={draft.requires_documents}
            onChange={(event) => set("requires_documents", event.target.checked)}
            disabled={saving}
          />
          Requires documents
        </label>
        <label>
          <input
            type="checkbox"
            checked={draft.restricted_archive_access}
            onChange={(event) => set("restricted_archive_access", event.target.checked)}
            disabled={saving}
          />
          Restricted archive access
        </label>
        <label>
          Description
          <textarea
            value={draft.description}
            onChange={(event) => set("description", event.target.value)}
            disabled={saving}
          />
        </label>
        <label>
          Benefits
          <textarea
            value={draft.benefits}
            onChange={(event) => set("benefits", event.target.value)}
            disabled={saving}
          />
        </label>
        <button type="submit" disabled={saving}>
          {saving ? "Saving…" : "Save plan"}
        </button>
        {editingId !== null ? (
          <button type="button" onClick={reset} disabled={saving}>
            Cancel
          </button>
        ) : null}
      </form>
    </section>
  )
}

function MembershipWorkspace() {
  const { user } = useAuth()
  return (
    <section>
      <h1>Membership</h1>
      <RequestQueue />
      {hasAnyRole(user, PLAN_MANAGER_ROLES) ? <PlanManager /> : null}
    </section>
  )
}

export default function MembershipStaffPage() {
  return (
    <RequireRole anyRole={APPROVER_ROLES}>
      <MembershipWorkspace />
    </RequireRole>
  )
}
