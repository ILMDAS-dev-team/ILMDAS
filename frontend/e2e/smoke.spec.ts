import { expect, test } from "@playwright/test"

test("public homepage loads with navigation and no staff links", async ({ page }) => {
  const response = await page.goto("/")
  expect(response?.ok()).toBeTruthy()
  await expect(
    page.getByRole("heading", { name: "A world of knowledge. A heritage to keep." })
  ).toBeVisible()
  const nav = page.getByRole("navigation", { name: "Public" })
  await expect(nav).toBeVisible()
  await expect(nav.getByRole("link", { name: "E-Book" })).toBeVisible()
  await expect(nav.getByRole("link", { name: "Catalogue" })).toBeVisible()
  await expect(nav.getByRole("link", { name: "Home" })).toHaveCSS("font-weight", "700")
  await expect(nav.getByRole("link", { name: "Home" })).toHaveCSS("font-size", "16px")
  const header = page.getByRole("banner")
  await expect(header.getByRole("link", { name: /IQQO Digital Library/ })).toBeVisible()
  await expect(header.getByRole("img", { name: "IQQO Digital Library logo" })).toBeVisible()
  await expect(header.getByRole("link", { name: "Facebook" })).toBeVisible()
  await expect(page.getByRole("region", { name: /hero picture slideshow/i })).toBeVisible()
  await expect(page.getByRole("button", { name: "Next hero picture" })).toBeVisible()
  await expect(page.getByRole("button", { name: "Slide 1 of 4" })).toBeVisible()
  await expect(page.getByRole("heading", { name: "What We Offer" })).toHaveCSS(
    "text-align",
    "center"
  )
  await expect(page.getByRole("heading", { name: "Learning & Research" })).toHaveCSS(
    "text-align",
    "center"
  )
  await expect(page.getByRole("heading", { name: "E-Books" })).toBeVisible()
  await expect(page.getByRole("heading", { name: "From ILMDAS" })).toBeVisible()
  await expect(
    page.getByRole("img", { name: "Oromo Irreechaa thanks-giving festival" })
  ).toBeVisible()
  await expect(page.getByRole("contentinfo")).toBeVisible()
  await expect(page.getByRole("contentinfo").getByRole("link", { name: "YouTube" })).toBeVisible()
  await expect(page.getByRole("link", { name: "Administration" })).toHaveCount(0)
  await expect(page.locator('a[href="/staff"]')).toHaveCount(0)
})

test("E-Book navigation opens the existing search route", async ({ page }) => {
  await page.goto("/")
  await page
    .getByRole("navigation", { name: "Public" })
    .getByRole("link", { name: "E-Book" })
    .click()
  await expect(page).toHaveURL(/\/opac/)
  await expect(page.getByRole("heading", { name: "E-Book", level: 1 })).toBeVisible()
})

test("Catalogue navigation opens the catalogue page", async ({ page }) => {
  await page.goto("/")
  await page
    .getByRole("navigation", { name: "Public" })
    .getByRole("link", { name: "Catalogue" })
    .click()
  await expect(page).toHaveURL(/\/catalogue$/)
  await expect(page.getByRole("heading", { name: "Catalogue", level: 1 })).toBeVisible()
  await expect(page.getByRole("search")).toHaveAttribute("action", "/opac")
})

test("brand logos sit on the left side of the header and footer", async ({ page }) => {
  await page.goto("/")
  const logoName = "IQQO Digital Library logo"
  const headerLogo = page.getByRole("banner").getByRole("img", { name: logoName })
  const footerLogo = page.getByRole("contentinfo").getByRole("img", { name: logoName })

  const headerBox = await headerLogo.boundingBox()
  expect(headerBox?.x).toBeLessThan(60)

  await footerLogo.scrollIntoViewIfNeeded()
  const footerBox = await footerLogo.boundingBox()
  expect(footerBox?.x).toBeLessThan(60)
})

test("back-to-top control returns the visitor to the top", async ({ page }) => {
  await page.goto("/")
  const button = page.getByRole("button", { name: "Back to top" })
  await expect(button).toHaveCount(0)

  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
  await expect(button).toBeVisible()
  await button.click()
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBeLessThan(120)
})

test("staff page redirects anonymous visitor to login", async ({ page }) => {
  await page.goto("/staff")
  await expect(page).toHaveURL(/\/login\?next=%2Fstaff$/)
  await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible()
})

test("staff sub-route redirects anonymous visitor to login", async ({ page }) => {
  await page.goto("/staff/catalogue")
  await expect(page).toHaveURL(/\/login\?next=%2Fstaff%2Fcatalogue$/)
  await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible()
})

test("old /sign-in links go to the login page", async ({ page }) => {
  await page.goto("/sign-in")
  await expect(page).toHaveURL(/\/login$/)
  await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible()
})
