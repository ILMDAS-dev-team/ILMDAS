type HeaderMap = Record<string, string>

export function createCorrelationId(): string {
  if (globalThis.crypto && typeof globalThis.crypto.randomUUID === "function") {
    return globalThis.crypto.randomUUID()
  }
  return `cid-${Date.now()}`
}

export function getCookie(name: string): string | null {
  if (typeof document === "undefined") {
    return null
  }
  const prefix = `${name}=`
  const match = document.cookie
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(prefix))
  if (!match) {
    return null
  }
  return decodeURIComponent(match.slice(prefix.length))
}

export function buildHeaders(
  headers: HeaderMap = {},
  correlationId = createCorrelationId()
): HeaderMap {
  const csrfToken = getCookie("csrftoken")
  return {
    Accept: "application/json",
    "X-Correlation-ID": correlationId,
    ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
    ...headers,
  }
}

export function apiBaseUrl(baseUrl?: string): string {
  return (baseUrl || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8010").replace(/\/$/, "")
}

export async function apiFetch(
  path: string,
  init: RequestInit = {},
  baseUrl?: string
): Promise<{ response: Response; correlationId: string }> {
  const correlationId = createCorrelationId()
  const response = await fetch(`${apiBaseUrl(baseUrl)}${path}`, {
    credentials: "include",
    ...init,
    headers: buildHeaders({ ...(init.headers as HeaderMap | undefined) }, correlationId),
  })
  return { response, correlationId }
}

export async function ensureCsrfCookie(baseUrl?: string): Promise<string | null> {
  const { response } = await apiFetch("/api/v1/auth/csrf/", { method: "GET" }, baseUrl)
  if (!response.ok) {
    return getCookie("csrftoken")
  }
  const body = (await response.json()) as { csrfToken?: string }
  return body.csrfToken || getCookie("csrftoken")
}

/**
 * Header carrying the token returned by the CSRF endpoint. Use this instead of relying on
 * `document.cookie`, which cannot see the API's cookie when the API is on another host.
 */
export function csrfHeader(token: string | null): HeaderMap {
  return token ? { "X-CSRFToken": token } : {}
}
