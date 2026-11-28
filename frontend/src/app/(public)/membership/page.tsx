import Link from "next/link"

export default function MembershipPage() {
  return (
    <section className="simple-page">
      <h1>Membership</h1>
      <p>
        Membership information and the sign-up workflow are published here when approved by ILMDAS.
        Existing members can sign in to manage their account.
      </p>
      <Link className="button button--dark" href="/login">
        Sign in
      </Link>
    </section>
  )
}
