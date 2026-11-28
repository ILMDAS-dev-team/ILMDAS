"use client"

import Link from "next/link"
import { FormEvent, useState } from "react"
import { errorFields, errorMessage, type FieldErrors } from "@/lib/apiErrors"
import { registerAccount } from "@/lib/registration"

type Values = {
  username: string
  email: string
  first_name: string
  last_name: string
  password: string
  confirm_password: string
  accept_terms: boolean
}

const EMPTY: Values = {
  username: "",
  email: "",
  first_name: "",
  last_name: "",
  password: "",
  confirm_password: "",
  accept_terms: false,
}

const FALLBACK_ERROR = "Your account could not be created. Try again."

function validate(values: Values): FieldErrors {
  const errors: FieldErrors = {}
  if (!values.username.trim()) errors.username = "Choose a username."
  if (!values.email.trim()) errors.email = "Enter your email address."
  if (!values.first_name.trim()) errors.first_name = "Enter your first name."
  if (!values.password) errors.password = "Choose a password." // pragma: allowlist secret
  if (values.password && values.password !== values.confirm_password) {
    errors.confirm_password = "The passwords don't match." // pragma: allowlist secret
  }
  if (!values.accept_terms) errors.accept_terms = "You must accept the terms to register."
  return errors
}

// Self-registration (ILMDAS-552). The account stays pending until the email is verified.
export function RegisterForm() {
  const [values, setValues] = useState<Values>(EMPTY)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null)

  function update<K extends keyof Values>(key: K, value: Values[K]) {
    setValues((current) => ({ ...current, [key]: value }))
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    const clientErrors = validate(values)
    setFieldErrors(clientErrors)
    if (Object.keys(clientErrors).length > 0) return

    setLoading(true)
    try {
      await registerAccount({
        username: values.username.trim(),
        email: values.email.trim(),
        first_name: values.first_name.trim(),
        last_name: values.last_name.trim(),
        password: values.password,
        accept_terms: values.accept_terms,
      })
      setRegisteredEmail(values.email.trim())
    } catch (caught) {
      setFieldErrors(errorFields(caught))
      setError(errorMessage(caught, FALLBACK_ERROR))
    } finally {
      setLoading(false)
    }
  }

  if (registeredEmail) {
    return (
      <section className="login-panel">
        <header className="login-intro">
          <h1>Check your email</h1>
          <p className="login-subtitle" role="status">
            We sent a link to {registeredEmail}. Open it to activate your account, then sign in.
          </p>
        </header>
        <p className="login-footer">
          <span>Already verified?</span>
          <Link href="/login">Sign in</Link>
        </p>
      </section>
    )
  }

  function field(
    key: "username" | "email" | "first_name" | "last_name" | "password" | "confirm_password",
    label: string,
    options: { type?: string; autoComplete?: string; optional?: boolean } = {}
  ) {
    const id = `register-${key}`
    const message = fieldErrors[key]
    return (
      <div className="login-field">
        <label htmlFor={id}>
          {label}
          {options.optional ? " (optional)" : ""}
        </label>
        <input
          id={id}
          name={key}
          type={options.type ?? "text"}
          autoComplete={options.autoComplete}
          value={values[key]}
          onChange={(event) => update(key, event.target.value)}
          disabled={loading}
          aria-invalid={message ? true : undefined}
          aria-describedby={message ? `${id}-error` : undefined}
        />
        {message ? (
          <p id={`${id}-error`} className="login-error">
            {message}
          </p>
        ) : null}
      </div>
    )
  }

  return (
    <section className="login-panel">
      <header className="login-intro">
        <h1>Create an account</h1>
        <p className="login-subtitle">
          Register to request a membership. You can browse the catalogue without an account.
        </p>
      </header>

      <form className="login-form" onSubmit={onSubmit} noValidate>
        <div className="login-field-group">
          {field("first_name", "First name", { autoComplete: "given-name" })}
          {field("last_name", "Last name", { autoComplete: "family-name", optional: true })}
          {field("email", "Email", { type: "email", autoComplete: "email" })}
          {field("username", "Username", { autoComplete: "username" })}
          {field("password", "Password", { type: "password", autoComplete: "new-password" })}
          {field("confirm_password", "Confirm password", {
            type: "password",
            autoComplete: "new-password",
          })}
          <p className="login-subtitle">Use at least 12 characters, not only numbers.</p>
        </div>

        <div className="login-field">
          <label className="login-remember">
            <input
              type="checkbox"
              name="accept_terms"
              checked={values.accept_terms}
              onChange={(event) => update("accept_terms", event.target.checked)}
              disabled={loading}
              aria-invalid={fieldErrors.accept_terms ? true : undefined}
              aria-describedby={fieldErrors.accept_terms ? "register-terms-error" : undefined}
            />
            I accept the library&apos;s terms of use.
          </label>
          {fieldErrors.accept_terms ? (
            <p id="register-terms-error" className="login-error">
              {fieldErrors.accept_terms}
            </p>
          ) : null}
        </div>

        {error ? (
          <p className="login-error" role="alert">
            {error}
          </p>
        ) : null}

        <button type="submit" className="login-submit" disabled={loading} aria-busy={loading}>
          {loading ? "Creating account…" : "Create account"}
        </button>

        <p className="login-footer">
          <span>Already have an account?</span>
          <Link href="/login">Sign in</Link>
        </p>
      </form>
    </section>
  )
}
