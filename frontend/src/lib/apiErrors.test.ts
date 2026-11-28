import { ApiRequestError, errorFields, errorMessage, readApiError, sendJson } from "@/lib/apiErrors"

jest.mock("@/lib/api", () => ({
  ...jest.requireActual("@/lib/api"),
  ensureCsrfCookie: jest.fn(),
  apiFetch: jest.fn(),
}))

import { apiFetch, ensureCsrfCookie } from "@/lib/api"

function fakeResponse(status: number, body?: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => {
      if (body === undefined) throw new Error("no body")
      return body
    },
  } as Response
}

describe("readApiError", () => {
  test("splits field errors from the non-field message", async () => {
    const error = await readApiError(
      fakeResponse(400, {
        code: "validation_error",
        errors: { email: ["Enter a valid email."], non_field_errors: ["Details are taken."] },
      }),
      "fallback"
    )
    expect(error).toBeInstanceOf(ApiRequestError)
    expect(error.status).toBe(400)
    expect(error.message).toBe("Details are taken.")
    expect(error.fieldErrors).toEqual({ email: "Enter a valid email." })
  })

  test("reads a list of errors, as conflicts return them", async () => {
    const error = await readApiError(
      fakeResponse(409, { code: "conflict", errors: ["Already in progress."] }),
      "fallback"
    )
    expect(error.message).toBe("Already in progress.")
  })

  test("uses a status message when there are no errors", async () => {
    const error = await readApiError(fakeResponse(429, { code: "rate_limit" }), "fallback")
    expect(error.message).toBe("Too many attempts. Wait a few minutes and try again.")
  })

  test("uses the fallback for an unknown status without a body", async () => {
    const error = await readApiError(fakeResponse(500), "Something went wrong.")
    expect(error.message).toBe("Something went wrong.")
  })

  test("keeps the fallback message when only field errors are given", async () => {
    const error = await readApiError(
      fakeResponse(400, { errors: { password: ["Too short."] } }),
      "Check the form."
    )
    expect(error.message).toBe("Check the form.")
    expect(error.fieldErrors).toEqual({ password: "Too short." }) // pragma: allowlist secret
  })
})

describe("sendJson", () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(ensureCsrfCookie as jest.Mock).mockResolvedValue("csrf-1")
  })

  test("posts JSON with the CSRF header and returns the body", async () => {
    ;(apiFetch as jest.Mock).mockResolvedValue({ response: fakeResponse(200, { detail: "ok" }) })
    await expect(sendJson("/api/v1/x/", { a: 1 }, "fallback")).resolves.toEqual({ detail: "ok" })
    expect(apiFetch).toHaveBeenCalledWith("/api/v1/x/", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": "csrf-1" },
      body: JSON.stringify({ a: 1 }),
    })
  })

  test("throws an ApiRequestError for a failed response", async () => {
    ;(apiFetch as jest.Mock).mockResolvedValue({
      response: fakeResponse(403, { code: "authorization_error" }),
    })
    await expect(sendJson("/api/v1/x/", {}, "fallback")).rejects.toMatchObject({
      status: 403,
      message: "You don't have permission to do this.",
    })
  })
})

test("errorMessage and errorFields fall back for unknown errors", () => {
  expect(errorMessage(new Error("boom"), "fallback")).toBe("fallback")
  expect(errorFields(new Error("boom"))).toEqual({})
  const known = new ApiRequestError("Known", 400, { email: "Bad" })
  expect(errorMessage(known, "fallback")).toBe("Known")
  expect(errorFields(known)).toEqual({ email: "Bad" })
})
