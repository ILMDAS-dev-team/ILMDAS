import { buildHeaders, createCorrelationId, csrfHeader, getCookie } from "@/lib/api"

test("the API client attaches a correlation identifier", () => {
  const headers = buildHeaders({ "Content-Type": "application/json" }, "cid-test")
  expect(headers["X-Correlation-ID"]).toBe("cid-test")
  expect(headers.Accept).toBe("application/json")
  expect(headers["Content-Type"]).toBe("application/json")
})

test("a correlation identifier is generated when the caller does not pass one", () => {
  const headers = buildHeaders()
  expect(typeof headers["X-Correlation-ID"]).toBe("string")
  expect(headers["X-Correlation-ID"].length > 0).toBe(true)
  expect(createCorrelationId().length > 0).toBe(true)
})

afterEach(() => {
  document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/"
})

test("getCookie returns null when the cookie is not set", () => {
  expect(getCookie("csrftoken")).toBeNull()
})

test("getCookie returns the decoded value of a set cookie", () => {
  document.cookie = "other=1; path=/"
  document.cookie = "csrftoken=abc%3D%3D123; path=/"
  expect(getCookie("csrftoken")).toBe("abc==123")
  document.cookie = "other=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/"
})

test("buildHeaders adds the CSRF cookie value when present", () => {
  document.cookie = "csrftoken=from-cookie; path=/"
  expect(buildHeaders({}, "cid")["X-CSRFToken"]).toBe("from-cookie")
})

test("an explicit CSRF token header wins over the cookie", () => {
  document.cookie = "csrftoken=from-cookie; path=/"
  expect(buildHeaders(csrfHeader("from-endpoint"), "cid")["X-CSRFToken"]).toBe("from-endpoint")
  expect(csrfHeader(null)).toEqual({})
})
