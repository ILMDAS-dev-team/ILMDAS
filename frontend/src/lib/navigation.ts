/** Full-page navigation, kept in one place so tests can replace it. */
export function navigateTo(path: string): void {
  window.location.assign(path)
}

/**
 * The `next` value from the query string, if it is a same-site path. Anything else
 * (absent, an absolute URL, or a protocol-relative "//host" path) falls back, which
 * prevents open redirects after sign-in.
 */
export function safeNextPath(next: string | string[] | undefined, fallback = "/"): string {
  const value = Array.isArray(next) ? next[0] : next
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.startsWith("/\\")) {
    return fallback
  }
  return value
}
