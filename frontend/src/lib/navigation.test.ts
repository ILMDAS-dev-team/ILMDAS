import { safeNextPath } from "@/lib/navigation"

test("keeps same-site paths", () => {
  expect(safeNextPath("/staff")).toBe("/staff")
  expect(safeNextPath("/staff/catalogue?page=2")).toBe("/staff/catalogue?page=2")
  expect(safeNextPath(["/staff", "/other"])).toBe("/staff")
})

test("falls back for missing or off-site targets", () => {
  expect(safeNextPath(undefined)).toBe("/")
  expect(safeNextPath("")).toBe("/")
  expect(safeNextPath("https://evil.example")).toBe("/")
  expect(safeNextPath("//evil.example")).toBe("/")
  expect(safeNextPath(String.raw`/\evil.example`)).toBe("/")
  expect(safeNextPath("staff", "/home")).toBe("/home")
})
