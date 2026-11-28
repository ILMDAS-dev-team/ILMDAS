import Link from "next/link"

export default function ArchivePage() {
  return (
    <section className="simple-page">
      <h1>Digital Archive</h1>
      <p>
        The archive shares approved historical documents, oral histories, manuscripts and research
        collections. Public materials are displayed here when approved by the archive team.
      </p>
      <p>
        Restricted materials are never shown to anonymous visitors. Sign in to check whether your
        account can access them.
      </p>
      <Link className="button button--dark" href="/login">
        Sign in
      </Link>
    </section>
  )
}
