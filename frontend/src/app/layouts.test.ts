import { readFileSync } from "fs"
import { join } from "path"

function read(relativePath: string) {
  return readFileSync(join(process.cwd(), relativePath), "utf8")
}

test("public shell has no administration or staff links", () => {
  const layout = read("src/app/(public)/layout.tsx")
  expect(layout.includes("Administration")).toBe(false)
  expect(layout.includes("/staff")).toBe(false)
  expect(layout.includes("IIIF status")).toBe(false)
  expect(layout.includes("Home")).toBe(true)
  expect(layout.includes("OPAC")).toBe(true)
})

test("staff shell reserves the module places", () => {
  const layout = read("src/app/(staff)/staff/layout.tsx")
  for (const label of [
    "Catalogue",
    "Circulation",
    "Membership",
    "Archive",
    "Publishing",
    "Reports",
    "Administration",
  ]) {
    expect(layout.includes(label)).toBe(true)
  }
})

test("staff layout sends visitors without a staff session to login", () => {
  const layout = read("src/app/(staff)/staff/layout.tsx")
  expect(layout.includes("useAuth()")).toBe(true)
  expect(layout.includes("isStaff(user)")).toBe(true)
  // Signed in without a staff role: denied in place, not sent back to login (no loop)
  expect(layout.includes("<AccessDenied />")).toBe(true)
  // Audit log link is admin-only, like Administration
  expect(layout.includes('"/staff/administration", "/staff/audit"')).toBe(true)
  expect(layout.includes("if (!user) {")).toBe(true)
  expect(layout.includes('redirect("/login?next=/staff")')).toBe(true)
})

test("shells fit a 360px viewport and a desktop width", () => {
  const css = read("src/app/globals.css")
  expect(css.includes("width: 100%")).toBe(true)
  expect(css.includes("box-sizing: border-box")).toBe(true)
  expect(css.includes("@media (max-width: 360px)")).toBe(true)
  expect(css.includes("max-width: 72rem")).toBe(true)
  const publicLayout = read("src/app/(public)/layout.tsx")
  const staffLayout = read("src/app/(staff)/staff/layout.tsx")
  expect(publicLayout.includes('className="shell"')).toBe(true)
  expect(staffLayout.includes('className="shell"')).toBe(true)
})
