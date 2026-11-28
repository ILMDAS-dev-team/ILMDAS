import { AuthShell } from "@/components/AuthShell"
import { RegisterForm } from "@/components/RegisterForm"

// Public self-registration (ILMDAS-552). New accounts start as guests.
export default function RegisterPage() {
  return (
    <AuthShell
      heading="Join the IQQO library."
      message="Create an account, verify your email, then choose a membership plan."
    >
      <RegisterForm />
    </AuthShell>
  )
}
