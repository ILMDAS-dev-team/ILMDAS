import { AuthShell } from "@/components/AuthShell"
import { LoginForm } from "@/components/LoginForm"

type SignInScreenProps = {
  title: string
  redirectTo: string
}

// Figma: "ILMDAS · Sign in — credential error" (node 80:2)
export function SignInScreen({ title, redirectTo }: SignInScreenProps) {
  return (
    <AuthShell
      heading="Your library, wherever you are."
      message="Sign in to manage loans, reservations and your digitised collection."
    >
      <LoginForm title={title} redirectTo={redirectTo} />
    </AuthShell>
  )
}
