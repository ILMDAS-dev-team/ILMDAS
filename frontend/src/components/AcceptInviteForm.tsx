"use client"

import Link from "next/link"
import { FormEvent, useState } from "react"
import { errorFields, errorMessage, type FieldErrors } from "@/lib/apiErrors"
import { acceptInvite } from "@/lib/registration"

type AcceptInviteFormProps = {
  uid: string
  token: string
}

// A new staff member sets their own password from the invite link (ILMDAS-551).
export function AcceptInviteForm({ uid, token }: AcceptInviteFormProps) {
  const [password, setPassword] = useState("")
  const [confirm, setConfirm] = useState("")
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [error, setError] = useState<string | null>(
    uid && token ? null : "This link is incomplete. Open the link from your email again."
  )
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    const clientErrors: FieldErrors = {}
    if (!password) clientErrors.password = "Choose a password." // pragma: allowlist secret
    if (password && password !== confirm) {
      clientErrors.confirm = "The passwords don't match." // pragma: allowlist secret
    }
    setFieldErrors(clientErrors)
    if (Object.keys(clientErrors).length > 0) return

    setLoading(true)
    try {
      await acceptInvite(uid, token, password)
      setDone(true)
    } catch (caught) {
      const fields = errorFields(caught)
      setFieldErrors(fields.password ? { password: fields.password } : {})
      // A bad or expired link comes back as a `token` field error.
      setError(fields.token ?? (fields.password ? null : errorMessage(caught, "Try again.")))
    } finally {
      setLoading(false)
    }
  }

  if (done) {
    return (
      <section className="login-panel">
        <header className="login-intro">
          <h1>Your password is set</h1>
          <p className="login-subtitle" role="status">
            You can now sign in with your username and new password.
          </p>
        </header>
        <Link className="login-submit" href="/login?next=/staff">
          Sign in
        </Link>
      </section>
    )
  }

  return (
    <section className="login-panel">
      <header className="login-intro">
        <h1>Set your password</h1>
        <p className="login-subtitle">Choose a password for your ILMDAS staff account.</p>
      </header>
      <form className="login-form" onSubmit={onSubmit} noValidate>
        <div className="login-field-group">
          <div className="login-field">
            <label htmlFor="invite-password">New password</label>
            <input
              id="invite-password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              disabled={loading}
              aria-invalid={fieldErrors.password ? true : undefined}
              aria-describedby={fieldErrors.password ? "invite-password-error" : undefined}
            />
            {fieldErrors.password ? (
              <p id="invite-password-error" className="login-error">
                {fieldErrors.password}
              </p>
            ) : null}
          </div>
          <div className="login-field">
            <label htmlFor="invite-confirm">Confirm password</label>
            <input
              id="invite-confirm"
              type="password"
              autoComplete="new-password"
              value={confirm}
              onChange={(event) => setConfirm(event.target.value)}
              disabled={loading}
              aria-invalid={fieldErrors.confirm ? true : undefined}
              aria-describedby={fieldErrors.confirm ? "invite-confirm-error" : undefined}
            />
            {fieldErrors.confirm ? (
              <p id="invite-confirm-error" className="login-error">
                {fieldErrors.confirm}
              </p>
            ) : null}
          </div>
          <p className="login-subtitle">Use at least 12 characters, not only numbers.</p>
        </div>
        {error ? (
          <p className="login-error" role="alert">
            {error}
          </p>
        ) : null}
        <button type="submit" className="login-submit" disabled={loading} aria-busy={loading}>
          {loading ? "Saving…" : "Set password"}
        </button>
      </form>
    </section>
  )
}
