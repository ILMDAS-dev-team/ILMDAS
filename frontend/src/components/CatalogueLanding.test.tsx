import { render, screen } from "@testing-library/react"
import { CatalogueLanding } from "@/components/CatalogueLanding"
import { LanguageProvider } from "@/context/LanguageContext"

test("catalogue page offers a search that uses the existing OPAC route", () => {
  render(
    <LanguageProvider>
      <CatalogueLanding />
    </LanguageProvider>
  )

  expect(screen.getByRole("heading", { name: "Catalogue", level: 1 })).toBeInTheDocument()
  expect(screen.getByRole("search")).toHaveAttribute("action", "/opac")
})
