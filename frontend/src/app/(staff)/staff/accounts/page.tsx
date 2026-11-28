"use client"

import { FormEvent, useState } from "react"
import { RequireRole } from "@/components/RequireRole"
import { errorFields, errorMessage, type FieldErrors } from "@/lib/apiErrors"
import { createStaffAccount } from "@/lib/registration"
import { ROLE_NAMES, ROLE_SYSTEM_ADMINISTRATOR, STAFF_ROLE_CODES } from "@/lib/roles"

type Draft = {
  username: string
  email: string
  first_name: string
  last_name: string
  roles: string[]
}

const EMPTY: Draft = { username: "", email: "", first_name: "", last_name: "", roles: [] }

// A system administrator registers a staff account; the person gets an invite email
// and sets their own password (ILMDAS-551).
function StaffAccountForm() {
  const [draft, setDraft] = useState<Draft>(EMPTY)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [invited, setInvited] = useState<string | null>(null)

  function set(key: Exclude<keyof Draft, "roles">, value: string) {
    setDraft((current) => ({ ...current, [key]: value }))
  }

  function toggleRole(code: string, checked: boolean) {
    setDraft((current) => ({
      ...current,
      roles: checked ? [...current.roles, code] : current.roles.filter((role) => role !== code),
    }))
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setInvited(null)
    const clientErrors: FieldErrors = {}
    if (!draft.username.trim()) clientErrors.username = "Enter a username."
    if (!draft.email.trim()) clientErrors.email = "Enter an email address."
    if (draft.roles.length === 0) clientErrors.roles = "Choose at least one role."
    setFieldErrors(clientErrors)
    if (Object.keys(clientErrors).length > 0) return

    setSaving(true)
    try {
      const account = await createStaffAccount({
        ...draft,
        username: draft.username.trim(),
        email: draft.email.trim(),
      })
      setInvited(account.email)
      setDraft(EMPTY)
    } catch (caught) {
      setFieldErrors(errorFields(caught))
      setError(errorMessage(caught, "The staff account could not be created."))
    } finally {
      setSaving(false)
    }
  }

  function text(key: Exclude<keyof Draft, "roles">, label: string, type = "text") {
    return (
      <label>
        {label}
        <input
          type={type}
          value={draft[key]}
          onChange={(event) => set(key, event.target.value)}
          disabled={saving}
          aria-invalid={fieldErrors[key] ? true : undefined}
        />
        {fieldErrors[key] ? <span role="alert">{fieldErrors[key]}</span> : null}
      </label>
    )
  }

  return (
    <section>
      <h1>Register a staff account</h1>
      <p>
        The new staff member gets an email with a link to set their own password. The account
        can&apos;t sign in until they do.
      </p>
      {invited ? <p role="status">Invite sent to {invited}.</p> : null}
      {error ? <p role="alert">{error}</p> : null}
      <form onSubmit={onSubmit} aria-label="Register a staff account" noValidate>
        {text("first_name", "First name")}
        {text("last_name", "Last name")}
        {text("email", "Email", "email")}
        {text("username", "Username")}
        <fieldset>
          <legend>Roles</legend>
          {STAFF_ROLE_CODES.map((code) => (
            <label key={code}>
              <input
                type="checkbox"
                checked={draft.roles.includes(code)}
                onChange={(event) => toggleRole(code, event.target.checked)}
                disabled={saving}
              />
              {ROLE_NAMES[code]}
            </label>
          ))}
          {fieldErrors.roles ? <span role="alert">{fieldErrors.roles}</span> : null}
        </fieldset>
        <button type="submit" disabled={saving} aria-busy={saving}>
          {saving ? "Creating…" : "Create account and send invite"}
        </button>
      </form>
    </section>
  )
}

export default function StaffAccountsPage() {
  return (
    <RequireRole role={ROLE_SYSTEM_ADMINISTRATOR}>
      <StaffAccountForm />
    </RequireRole>
  )
}
