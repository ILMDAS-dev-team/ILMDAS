import Image from "next/image"
import { Abyssinica_SIL } from "next/font/google"
import type { ReactNode } from "react"

const ethiopic = Abyssinica_SIL({
  subsets: ["ethiopic"],
  weight: "400",
  display: "swap",
})

type AuthShellProps = {
  heading: string
  message: string
  children: ReactNode
}

// Figma: the two-column layout of "ILMDAS · Sign in" (node 80:2), shared by the
// sign-in, registration, email-verification and invite screens.
export function AuthShell({ heading, message, children }: AuthShellProps) {
  return (
    <div className="auth-split">
      <aside className="auth-welcome">
        <div className="auth-brand">
          <Image src="/brand/iqqo-logo.png" alt="IQQO logo" width={118} height={118} priority />
          <span>ILMDAS</span>
        </div>
        <div className="auth-welcome-message">
          <h2>{heading}</h2>
          <p>{message}</p>
        </div>
        <p className="auth-languages">
          Afaan Oromoo · English ·{" "}
          <span lang="am" className={ethiopic.className}>
            አማርኛ
          </span>
        </p>
      </aside>
      <main className="auth-form-side">{children}</main>
    </div>
  )
}
