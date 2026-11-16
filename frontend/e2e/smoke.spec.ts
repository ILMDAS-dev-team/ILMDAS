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

test("staff page shows the catalogue place", async ({ page }) => {
  const response = await page.goto("/staff")
  expect(response?.ok()).toBeTruthy()
  await expect(page.getByRole("link", { name: "Catalogue" })).toBeVisible()
})
