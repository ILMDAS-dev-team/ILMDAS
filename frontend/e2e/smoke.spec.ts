import { expect, test } from "@playwright/test"

test("public page loads without staff links", async ({ page }) => {
  const response = await page.goto("/")
  expect(response?.ok()).toBeTruthy()
  await expect(
    page.getByRole("heading", { name: "Integrated Library Management and Digital Archive System" })
  ).toBeVisible()
  await expect(page.getByRole("link", { name: "Administration" })).toHaveCount(0)
  await expect(page.getByRole("link", { name: "Catalogue" })).toHaveCount(0)
  await expect(page.locator('a[href="/staff"]')).toHaveCount(0)
})

test("staff page redirects anonymous visitor to sign-in", async ({ page }) => {
  await page.goto("/staff")
  await expect(page).toHaveURL(/.*\/sign-in.*/)
  await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible()
})

test("staff sub-route redirects anonymous visitor to sign-in", async ({ page }) => {
  await page.goto("/staff/catalogue")
  await expect(page).toHaveURL(/.*\/sign-in.*/)
  await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible()
})
