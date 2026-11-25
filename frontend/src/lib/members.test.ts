import { fetchMemberRecord, normalizeMemberId, type MemberRecord } from "@/lib/members"

const member: MemberRecord = {
  id: 7,
  username: "member1",
  email: "member1@example.test",
  first_name: "",
  last_name: "",
  status: "suspended",
  role: "member",
  membership: {
    id: 1,
    category: { id: 1, code: "adult", name: "Adult", isActive: true },
    joinedAt: "2026-01-01T00:00:00Z",
  },
  borrowingEligibility: {
    eligible: false,
    reason: "member_suspended",
    message: "Not eligible to borrow.",
  },
}

const originalFetch = global.fetch

afterEach(() => {
  global.fetch = originalFetch
  jest.restoreAllMocks()
})

function response(status: number, body?: unknown): Response {
  return {
    status,
    ok: status >= 200 && status < 300,
    json: async () => body,
  } as Response
}

test("normalizeMemberId accepts only positive integer IDs", () => {
  expect(normalizeMemberId("7")).toBe("7")
  expect(normalizeMemberId(" 12 ")).toBe("12")
  expect(normalizeMemberId("0")).toBeNull()
  expect(normalizeMemberId("-1")).toBeNull()
  expect(normalizeMemberId("1/../2")).toBeNull()
  expect(normalizeMemberId("../2")).toBeNull()
  expect(normalizeMemberId("abc")).toBeNull()
  expect(normalizeMemberId("")).toBeNull()
  expect(normalizeMemberId(undefined)).toBeNull()
})

test("fetchMemberRecord forwards the staff session cookie server-side", async () => {
  const fetchMock = jest.fn().mockResolvedValue(response(200, member))
  global.fetch = fetchMock as unknown as typeof fetch

  const result = await fetchMemberRecord("7", "session-abc", "http://api.internal")

  expect(result).toEqual({ status: "ok", member })
  expect(fetchMock).toHaveBeenCalledTimes(1)

  const [url, options] = fetchMock.mock.calls[0] as [
    string,
    { headers: Record<string, string>; cache: string },
  ]
  expect(url).toBe("http://api.internal/api/v1/members/7/")
  expect(options.cache).toBe("no-store")
  expect(options.headers.Cookie).toBe("sessionid=session-abc")
})

test.each([
  [401, "unauthenticated"],
  [403, "forbidden"],
  [404, "not_found"],
  [500, "error"],
])("fetchMemberRecord maps status %s to %s", async (status, expected) => {
  global.fetch = jest.fn().mockResolvedValue(response(status)) as unknown as typeof fetch

  await expect(fetchMemberRecord("7", "session-abc")).resolves.toEqual({ status: expected })
})

test("fetchMemberRecord maps network failures to a safe error", async () => {
  global.fetch = jest.fn().mockRejectedValue(new Error("network down")) as unknown as typeof fetch

  await expect(fetchMemberRecord("7", "session-abc")).resolves.toEqual({ status: "error" })
})

test("fetchMemberRecord rejects an invalid member ID before making a request", async () => {
  const fetchMock = jest.fn()
  global.fetch = fetchMock as unknown as typeof fetch

  await expect(fetchMemberRecord("1/../2", "session-abc")).resolves.toEqual({ status: "error" })
  expect(fetchMock).not.toHaveBeenCalled()
})
