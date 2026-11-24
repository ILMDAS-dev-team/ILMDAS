"use client"

import { FormEvent, useState } from "react"
import { apiFetch, ensureCsrfCookie } from "@/lib/api"

const GENERIC_ERROR = "Sign-in failed. Check your details and try again."

type LoginFormProps = {
  title: string
  redirectTo: string
}

export function LoginForm({ title, redirectTo }: LoginFormProps) {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    if (!username.trim() || !password) {
      setError("Username and password are required.")
      return
    }

    setLoading(true)
    try {
      await ensureCsrfCookie()
      const { response } = await apiFetch("/api/v1/auth/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim(), password }),
      })
      if (!response.ok) {
        setError(GENERIC_ERROR)
        return
      }
      window.location.assign(redirectTo)
    } catch {
      setError(GENERIC_ERROR)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="login-panel">
      <h1>{title}</h1>
      <form className="login-form" onSubmit={onSubmit} noValidate>
        <label>
          Username
          <input
            name="username"
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            disabled={loading}
          />
        </label>
        <label>
          Password
          <input
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            disabled={loading}
          />
        </label>
        {error ? (
          <p className="login-error" role="alert">
            {error}
          </p>
        ) : null}
        <button type="submit" disabled={loading}>
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </section>
  )
}
