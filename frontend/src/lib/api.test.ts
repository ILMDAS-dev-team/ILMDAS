import { buildHeaders, createCorrelationId } from "@/lib/api"

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
