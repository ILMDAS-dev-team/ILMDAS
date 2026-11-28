import { render, screen } from "@testing-library/react"
import { HomeGallery } from "@/components/HomeGallery"
import { LanguageProvider } from "@/context/LanguageContext"

test("shows the supplied homepage images with accessible labels", () => {
  render(
    <LanguageProvider>
      <HomeGallery />
    </LanguageProvider>
  )

  expect(screen.getByRole("heading", { name: "From ILMDAS" })).toBeInTheDocument()
  expect(screen.getAllByRole("img")).toHaveLength(4)
  expect(screen.getByAltText("Oromo Irreechaa thanks-giving festival")).toBeInTheDocument()
})
