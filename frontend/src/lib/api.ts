type HeaderMap = Record<string, string>

export function createCorrelationId(): string {
  if (globalThis.crypto && typeof globalThis.crypto.randomUUID === "function") {
    return globalThis.crypto.randomUUID()
  }
  return `cid-${Date.now()}`
}

export function buildHeaders(
  headers: HeaderMap = {},
  correlationId = createCorrelationId()
): HeaderMap {
  return {
    Accept: "application/json",
    "X-Correlation-ID": correlationId,
    ...headers,
  }
}

export async function apiFetch(
  path: string,
  init: RequestInit = {},
  baseUrl?: string
): Promise<{ response: Response; correlationId: string }> {
  const correlationId = createCorrelationId()
  const root = (baseUrl || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8010").replace(
    /\/$/,
    ""
  )
  const response = await fetch(`${root}${path}`, {
    ...init,
    headers: buildHeaders({ ...(init.headers as HeaderMap | undefined) }, correlationId),
  })
  return { response, correlationId }
}
