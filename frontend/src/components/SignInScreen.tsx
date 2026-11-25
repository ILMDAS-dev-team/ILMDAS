import Image from "next/image"
import { Abyssinica_SIL } from "next/font/google"
import { LoginForm } from "@/components/LoginForm"

const ethiopic = Abyssinica_SIL({
  subsets: ["ethiopic"],
  weight: "400",
  display: "swap",
})

type SignInScreenProps = {
  title: string
  redirectTo: string
}

// Figma: "ILMDAS · Sign in — credential error" (node 80:2)
export function SignInScreen({ title, redirectTo }: SignInScreenProps) {
  return (
    <div className="auth-split">
      <aside className="auth-welcome">
        <div className="auth-brand">
          <Image src="/brand/iqqo-logo.png" alt="IQQO logo" width={118} height={118} priority />
          <span>ILMDAS</span>
        </div>
        <div className="auth-welcome-message">
          <h2>Your library, wherever you are.</h2>
          <p>Sign in to manage loans, reservations and your digitised collection.</p>
        </div>
        <p className="auth-languages">
          Afaan Oromoo · English ·{" "}
          <span lang="am" className={ethiopic.className}>
            አማርኛ
          </span>
        </p>
      </aside>
      <main className="auth-form-side">
        <LoginForm title={title} redirectTo={redirectTo} />
      </main>
    </div>
  )
}
