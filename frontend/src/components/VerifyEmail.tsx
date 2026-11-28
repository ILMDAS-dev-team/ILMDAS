"use client"

import Link from "next/link"
import { FormEvent, useEffect, useRef, useState } from "react"
import { errorMessage } from "@/lib/apiErrors"
import { resendVerification, verifyEmail } from "@/lib/registration"

type VerifyEmailProps = {
  uid: string
  token: string
}

type State = "verifying" | "verified" | "failed"

// Activates a self-registered account from the emailed link (ILMDAS-552).
export function VerifyEmail({ uid, token }: VerifyEmailProps) {
  const [state, setState] = useState<State>(uid && token ? "verifying" : "failed")
  const [error, setError] = useState<string | null>(
    uid && token ? null : "This link is incomplete. Open the link from your email again."
  )
  const [email, setEmail] = useState("")
  const [resendMessage, setResendMessage] = useState<string | null>(null)
  const [resending, setResending] = useState(false)
  // Links work once, so never post the same link twice (React runs effects twice in dev).
  const started = useRef(false)

  useEffect(() => {
    if (!uid || !token || started.current) return
    started.current = true
    verifyEmail(uid, token)
      .then(() => setState("verified"))
      .catch((caught) => {
        setState("failed")
        setError(errorMessage(caught, "This link is invalid or has expired."))
      })
  }, [uid, token])

  async function onResend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!email.trim()) return
    setResending(true)
    try {
      const { detail } = await resendVerification(email.trim())
      setResendMessage(detail)
    } catch (caught) {
      setResendMessage(errorMessage(caught, "No new link could be sent. Try again later."))
    } finally {
      setResending(false)
    }
  }

  return (
    <section className="login-panel">
      <header className="login-intro">
        <h1>Verify your email</h1>
        {state === "verifying" ? <p className="login-subtitle">Checking your link…</p> : null}
        {state === "verified" ? (
          <p className="login-subtitle" role="status">
            Your email is verified and your account is active.
          </p>
        ) : null}
        {state === "failed" && error ? (
          <p className="login-error" role="alert">
            {error}
          </p>
        ) : null}
      </header>

      {state === "verified" ? (
        <Link className="login-submit" href="/login">
          Sign in
        </Link>
      ) : null}

      {state === "failed" ? (
        <form className="login-form" onSubmit={onResend} noValidate aria-label="Send a new link">
          <div className="login-field">
            <label htmlFor="verify-email-address">Email address</label>
            <input
              id="verify-email-address"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              disabled={resending}
            />
          </div>
          {resendMessage ? (
            <p className="login-subtitle" role="status">
              {resendMessage}
            </p>
          ) : null}
          <button type="submit" className="login-submit" disabled={resending} aria-busy={resending}>
            {resending ? "Sending…" : "Send a new link"}
          </button>
        </form>
      ) : null}
    </section>
  )
}
