import { auditQuery } from "@/lib/audit"

test("builds the filter query string", () => {
  expect(auditQuery({})).toBe("")
  expect(
    auditQuery({ actor: " carol ", action: "auth.", dateFrom: "2026-11-01", dateTo: "2026-11-30" })
  ).toBe("?actor=carol&action=auth.&date_from=2026-11-01&date_to=2026-11-30")
  expect(auditQuery({ page: 1 })).toBe("")
  expect(auditQuery({ page: 3 })).toBe("?page=3")
})
