import { AuthShell } from "@/components/AuthShell"
import { VerifyEmail } from "@/components/VerifyEmail"

type VerifyEmailPageProps = {
  searchParams: Promise<{ uid?: string | string[]; token?: string | string[] }>
}

function single(value: string | string[] | undefined): string {
  return Array.isArray(value) ? (value[0] ?? "") : (value ?? "")
}

// The link in the verification email lands here (ILMDAS-552).
export default async function VerifyEmailPage({ searchParams }: VerifyEmailPageProps) {
  const { uid, token } = await searchParams
  return (
    <AuthShell heading="Almost there." message="Verifying your email activates your account.">
      <VerifyEmail uid={single(uid)} token={single(token)} />
    </AuthShell>
  )
}
