"use client"

import { FormEvent, useState } from "react"
import { apiFetch, csrfHeader, ensureCsrfCookie } from "@/lib/api"
import { navigateTo } from "@/lib/navigation"

const GENERIC_ERROR = "Email or password is not correct. Try again."

type LoginFormProps = {
  title: string
  redirectTo: string
}

type FieldErrors = {
  username?: string
  password?: string
}

// Figma: "Sign-in panel" (node 80:4)
export function LoginForm({ title, redirectTo }: LoginFormProps) {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    const nextFieldErrors: FieldErrors = {}
    if (!username.trim()) {
      nextFieldErrors.username = "Enter your email or member ID."
    }
    if (!password) {
      nextFieldErrors.password = "Enter your password." // pragma: allowlist secret
    }
    setFieldErrors(nextFieldErrors)
    if (nextFieldErrors.username || nextFieldErrors.password) {
      return
    }

    setLoading(true)
    try {
      const csrfToken = await ensureCsrfCookie()
      const { response } = await apiFetch("/api/v1/auth/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...csrfHeader(csrfToken) },
        body: JSON.stringify({ username: username.trim(), password }),
      })
      if (!response.ok) {
        // Generic message: never reveal whether the account exists or is inactive.
        setError(GENERIC_ERROR)
        return
      }
      navigateTo(redirectTo)
    } catch {
      setError(GENERIC_ERROR)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="login-panel">
      <header className="login-intro">
        <h1>{title}</h1>
        <p className="login-subtitle">Use your library account or staff credentials.</p>
      </header>

      <form className="login-form" onSubmit={onSubmit} noValidate>
        <div className="login-field">
          <label htmlFor="login-username">Email or member ID</label>
          <input
            id="login-username"
            name="username"
            autoComplete="username"
            placeholder="e.g. name@library.et"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            disabled={loading}
            aria-invalid={fieldErrors.username ? true : undefined}
            aria-describedby={fieldErrors.username ? "login-username-error" : undefined}
          />
          {fieldErrors.username ? (
            <p id="login-username-error" className="login-error">
              {fieldErrors.username}
            </p>
          ) : null}
        </div>

        <div className="login-field-group">
          <div className="login-field">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              disabled={loading}
              aria-invalid={fieldErrors.password ? true : undefined}
              aria-describedby={
                fieldErrors.password ? "login-password-error" : error ? "login-error" : undefined
              }
            />
            {fieldErrors.password ? (
              <p id="login-password-error" className="login-error">
                {fieldErrors.password}
              </p>
            ) : null}
          </div>
          {error ? (
            <p id="login-error" className="login-error" role="alert">
              {error}
            </p>
          ) : null}
        </div>

        <div className="login-options">
          {/* Keep me signed in — placeholder until session length is configurable */}
          <label className="login-remember">
            <input type="checkbox" disabled />
            Keep me signed in on this device
          </label>
          {/* Password reset is out of scope for ILMDAS-27 */}
          <a href="#" onClick={(e) => e.preventDefault()}>
            Forgot password?
          </a>
        </div>

        <button type="submit" className="login-submit" disabled={loading} aria-busy={loading}>
          {loading ? "Signing in…" : "Sign in"}
        </button>

        <p className="login-footer">
          <span>New member?</span>
          {/* Membership sign-up is a later ticket */}
          <a href="#" onClick={(e) => e.preventDefault()}>
            Create an account
          </a>
        </p>
      </form>
    </section>
  )
}
