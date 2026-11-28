/**
 * Reading the backend's error body, and small JSON request helpers (ILMDAS-549).
 *
 * The backend returns `{ code, message, correlationId, errors? }`. `errors` is either a
 * field map (`{ email: ["..."], non_field_errors: ["..."] }`) or a list of messages.
 */

import { apiFetch, csrfHeader, ensureCsrfCookie } from "@/lib/api"

export type FieldErrors = Record<string, string>

export class ApiRequestError extends Error {
  status: number
  fieldErrors: FieldErrors

  constructor(message: string, status: number, fieldErrors: FieldErrors = {}) {
    super(message)
    this.name = "ApiRequestError"
    this.status = status
    this.fieldErrors = fieldErrors
  }
}

const STATUS_MESSAGES: Record<number, string> = {
  401: "Sign in to continue.",
  403: "You don't have permission to do this.",
  404: "This item could not be found.",
  429: "Too many attempts. Wait a few minutes and try again.",
}

function firstMessage(value: unknown): string | undefined {
  if (typeof value === "string") return value
  if (Array.isArray(value)) return value.find((item) => typeof item === "string")
  return undefined
}

/** Turn a failed response into a message plus per-field messages. */
export async function readApiError(response: Response, fallback: string): Promise<ApiRequestError> {
  let body: { errors?: unknown } = {}
  try {
    body = (await response.json()) as { errors?: unknown }
  } catch {
    // No JSON body: fall through to the status message.
  }

  const fieldErrors: FieldErrors = {}
  let message: string | undefined
  const errors = body.errors
  if (Array.isArray(errors)) {
    message = firstMessage(errors)
  } else if (errors && typeof errors === "object") {
    for (const [field, value] of Object.entries(errors as Record<string, unknown>)) {
      const text = firstMessage(value)
      if (!text) continue
      if (field === "non_field_errors" || field === "detail") {
        message = message ?? text
      } else {
        fieldErrors[field] = text
      }
    }
  }

  if (!message && Object.keys(fieldErrors).length === 0) {
    message = STATUS_MESSAGES[response.status]
  }
  return new ApiRequestError(message ?? fallback, response.status, fieldErrors)
}

/** GET a JSON resource, throwing an ApiRequestError when the response is not ok. */
export async function getJson<T>(path: string, fallback: string): Promise<T> {
  const { response } = await apiFetch(path, { method: "GET" })
  if (!response.ok) {
    throw await readApiError(response, fallback)
  }
  return (await response.json()) as T
}

/** Send JSON with a fresh CSRF token, throwing an ApiRequestError when not ok. */
export async function sendJson<T>(
  path: string,
  body: unknown,
  fallback: string,
  method: "POST" | "PATCH" | "PUT" = "POST"
): Promise<T> {
  const csrfToken = await ensureCsrfCookie()
  const { response } = await apiFetch(path, {
    method,
    headers: { "Content-Type": "application/json", ...csrfHeader(csrfToken) },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!response.ok) {
    throw await readApiError(response, fallback)
  }
  return (await response.json()) as T
}

/** The message to show for any error thrown by the helpers above. */
export function errorMessage(error: unknown, fallback: string): string {
  return error instanceof ApiRequestError ? error.message : fallback
}

/** Per-field messages for any error thrown by the helpers above. */
export function errorFields(error: unknown): FieldErrors {
  return error instanceof ApiRequestError ? error.fieldErrors : {}
}
