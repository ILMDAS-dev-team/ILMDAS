import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { verifyStaffSession } from "@/lib/auth"
import {
  fetchMemberRecord,
  normalizeMemberId,
  type MemberLookupResult,
  type MemberRecord,
} from "@/lib/members"

interface MembershipPageProps {
  searchParams: Promise<{ memberId?: string }>
}

function LookupMessage({ result }: { result: MemberLookupResult }) {
  switch (result.status) {
    case "unauthenticated":
      return (
        <p role="alert">
          Your staff session has expired. <a href="/sign-in">Sign in again</a>.
        </p>
      )
    case "forbidden":
      return <p role="alert">You do not have permission to view member records.</p>
    case "not_found":
      return <p role="alert">Member record not found.</p>
    case "error":
      return <p role="alert">The member record could not be loaded. Try again.</p>
    case "ok":
      return null
  }
}

function MemberSummary({ member }: { member: MemberRecord }) {
  const eligibility = member.borrowingEligibility
  const category = member.membership?.category
  const eligibilityClass = eligibility.eligible
    ? "eligibility eligibility-eligible"
    : "eligibility eligibility-denied"

  return (
    <article className="member-record" aria-labelledby="member-record-heading">
      <h2 id="member-record-heading">Member: {member.username}</h2>

      <dl className="member-facts">
        <div>
          <dt>Account status</dt>
          <dd>{member.status}</dd>
        </div>
        <div>
          <dt>Membership category</dt>
          <dd>{category?.name ?? "No membership record"}</dd>
        </div>
        <div>
          <dt>Category status</dt>
          <dd>{category ? (category.isActive ? "Active" : "Inactive") : "Not assigned"}</dd>
        </div>
      </dl>

      <p className={eligibilityClass} role="status">
        {eligibility.message}
      </p>

      {eligibility.reason ? (
        <p className="eligibility-reason">
          Reason code: <code>{eligibility.reason}</code>
        </p>
      ) : null}
    </article>
  )
}

export default async function StaffMembershipPage({ searchParams }: MembershipPageProps) {
  const isAuthenticated = await verifyStaffSession()
  if (!isAuthenticated) {
    redirect("/sign-in")
  }

  const { memberId: rawMemberId } = await searchParams
  const memberId = normalizeMemberId(rawMemberId)
  let lookup: MemberLookupResult | null = null

  if (memberId) {
    const sessionId = (await cookies()).get("sessionid")?.value
    if (!sessionId) {
      redirect("/sign-in")
    }
    lookup = await fetchMemberRecord(memberId, sessionId)
  }

  return (
    <section>
      <h1>Membership</h1>
      <p>Look up a member record to check borrowing eligibility. This information is staff-only.</p>

      <form className="member-lookup" method="get" action="/staff/membership">
        <div>
          <label htmlFor="memberId">Member ID</label>
          <input
            id="memberId"
            name="memberId"
            type="text"
            inputMode="numeric"
            pattern="[0-9]+"
            defaultValue={rawMemberId ?? ""}
            required
          />
        </div>
        <button type="submit">Check eligibility</button>
      </form>

      {rawMemberId && !memberId ? <p role="alert">Enter a numeric member ID.</p> : null}

      {lookup ? <LookupMessage result={lookup} /> : null}
      {lookup?.status === "ok" ? <MemberSummary member={lookup.member} /> : null}
    </section>
  )
}
