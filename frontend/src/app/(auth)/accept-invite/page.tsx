import { AcceptInviteForm } from "@/components/AcceptInviteForm"
import { AuthShell } from "@/components/AuthShell"

type AcceptInvitePageProps = {
  searchParams: Promise<{ uid?: string | string[]; token?: string | string[] }>
}

function single(value: string | string[] | undefined): string {
  return Array.isArray(value) ? (value[0] ?? "") : (value ?? "")
}

// The link in a staff invite email lands here (ILMDAS-551).
export default async function AcceptInvitePage({ searchParams }: AcceptInvitePageProps) {
  const { uid, token } = await searchParams
  return (
    <AuthShell
      heading="Welcome to the ILMDAS team."
      message="An administrator has created a staff account for you."
    >
      <AcceptInviteForm uid={single(uid)} token={single(token)} />
    </AuthShell>
  )
}
