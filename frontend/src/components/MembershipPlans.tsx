"use client"

import Link from "next/link"
import { ChangeEvent, useCallback, useEffect, useState } from "react"
import { useAuth } from "@/context/AuthContext"
import { errorMessage } from "@/lib/apiErrors"
import {
  fetchMyMembership,
  fetchPlans,
  isOpenRequest,
  REQUEST_STATUS_LABELS,
  requestPlan,
  uploadDocument,
  type MembershipRequest,
  type MyMembership,
  type Plan,
} from "@/lib/membership"

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString()
}

function durationLabel(months: number): string {
  if (months % 12 === 0) {
    const years = months / 12
    return years === 1 ? "1 year" : `${years} years`
  }
  return months === 1 ? "1 month" : `${months} months`
}

function OpenRequestPanel({
  request,
  onChanged,
}: {
  request: MembershipRequest
  onChanged: () => Promise<void>
}) {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function onFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return
    setUploading(true)
    setError(null)
    try {
      await uploadDocument(request.id, file)
      await onChanged()
    } catch (caught) {
      setError(errorMessage(caught, "The document could not be uploaded."))
    } finally {
      setUploading(false)
      event.target.value = ""
    }
  }

  return (
    <div>
      <p>
        You requested the <strong>{request.plan.name}</strong> plan ({request.currency}{" "}
        {request.amount}). Status: <strong>{REQUEST_STATUS_LABELS[request.status]}</strong>.
      </p>
      {request.status === "awaiting_payment" ? (
        <p>Pay at the library desk. Staff will record the payment and review your request.</p>
      ) : null}
      {request.status === "awaiting_approval" ? (
        <p>Your payment is recorded. Staff will review your request soon.</p>
      ) : null}

      {request.plan.requires_documents ? (
        <div>
          <p>This plan needs supporting documents, such as an ID card (PDF, JPEG or PNG).</p>
          {request.documents.length > 0 ? (
            <ul aria-label="Uploaded documents">
              {request.documents.map((document) => (
                <li key={document.id}>{document.original_name}</li>
              ))}
            </ul>
          ) : null}
          <label>
            Upload a document{" "}
            <input
              type="file"
              accept="application/pdf,image/jpeg,image/png"
              onChange={onFile}
              disabled={uploading}
            />
          </label>
          {uploading ? <p>Uploading…</p> : null}
        </div>
      ) : null}
      {error ? <p role="alert">{error}</p> : null}
    </div>
  )
}

function MyMembershipPanel({
  membership,
  onChanged,
}: {
  membership: MyMembership
  onChanged: () => Promise<void>
}) {
  const open = membership.requests.find(isOpenRequest)
  const latest = membership.requests[0]

  return (
    <section aria-labelledby="my-membership-heading">
      <h2 id="my-membership-heading">My membership</h2>
      {membership.subscription ? (
        <p>
          You are a member on the <strong>{membership.subscription.plan.name}</strong> plan until{" "}
          {formatDate(membership.subscription.ends_at)}.
        </p>
      ) : open ? (
        <OpenRequestPanel request={open} onChanged={onChanged} />
      ) : latest?.status === "rejected" ? (
        <p>
          Your last request was not approved: {latest.rejection_reason} You can request a plan again
          below.
        </p>
      ) : (
        <p>You don&apos;t have a membership yet. Choose a plan below.</p>
      )}
    </section>
  )
}

// Public plan list with the signed-in account's own membership (ILMDAS-553, ILMDAS-554).
export function MembershipPlans() {
  const { user, loading: authLoading } = useAuth()
  const [plans, setPlans] = useState<Plan[] | null>(null)
  const [membership, setMembership] = useState<MyMembership | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [requesting, setRequesting] = useState<string | null>(null)

  const loadMembership = useCallback(async () => {
    try {
      setMembership(await fetchMyMembership())
    } catch (caught) {
      setError(errorMessage(caught, "Could not load your membership."))
    }
  }, [])

  useEffect(() => {
    fetchPlans()
      .then(setPlans)
      .catch((caught) => setError(errorMessage(caught, "Could not load membership plans.")))
  }, [])

  useEffect(() => {
    if (authLoading) return
    if (user) {
      void loadMembership()
    } else {
      setMembership(null)
    }
  }, [authLoading, user, loadMembership])

  async function onRequest(plan: Plan) {
    setRequesting(plan.slug)
    setError(null)
    try {
      await requestPlan(plan.slug)
      await loadMembership()
    } catch (caught) {
      setError(errorMessage(caught, "Could not request this plan."))
    } finally {
      setRequesting(null)
    }
  }

  const busy =
    membership !== null &&
    (membership.subscription !== null || membership.requests.some(isOpenRequest))

  return (
    <section className="simple-page">
      <h1>Membership</h1>
      <p>
        Members can borrow items and use member-only services. Choose a plan, pay at the library,
        and staff will activate your membership.
      </p>

      {error ? <p role="alert">{error}</p> : null}

      {!authLoading && !user ? (
        <p>
          <Link href="/register">Create an account</Link> or{" "}
          <Link href="/login?next=/membership">sign in</Link> to request a membership.
        </p>
      ) : null}

      {user && membership ? (
        <MyMembershipPanel membership={membership} onChanged={loadMembership} />
      ) : null}

      <h2>Plans</h2>
      {plans === null && !error ? <p>Loading plans…</p> : null}
      {plans !== null && plans.length === 0 ? <p>No membership plans are available yet.</p> : null}
      {plans !== null && plans.length > 0 ? (
        <ul className="card-grid card-grid--three" aria-label="Membership plans">
          {plans.map((plan) => (
            <li key={plan.id} className="content-card">
              <h3>{plan.name}</h3>
              <p>
                <strong>{plan.price_display}</strong> for {durationLabel(plan.duration_months)}
              </p>
              {plan.description ? <p>{plan.description}</p> : null}
              <ul>
                <li>Borrow up to {plan.loan_limit} items at a time</li>
                {plan.restricted_archive_access ? (
                  <li>Access to restricted archive items</li>
                ) : null}
                {plan.requires_documents ? <li>Needs supporting documents</li> : null}
              </ul>
              {plan.benefits ? <p>{plan.benefits}</p> : null}
              {user ? (
                <button
                  type="button"
                  className="button button--dark"
                  onClick={() => void onRequest(plan)}
                  disabled={busy || requesting !== null}
                  aria-busy={requesting === plan.slug}
                >
                  {requesting === plan.slug ? "Requesting…" : "Request this plan"}
                </button>
              ) : (
                <Link className="button button--dark" href="/login?next=/membership">
                  Sign in to request
                </Link>
              )}
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  )
}
