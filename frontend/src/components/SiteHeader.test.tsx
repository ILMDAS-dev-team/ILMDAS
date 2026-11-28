import { fireEvent, render, screen } from "@testing-library/react"
import { SiteHeader } from "@/components/SiteHeader"
import { LanguageProvider } from "@/context/LanguageContext"

jest.mock("next/navigation", () => ({ usePathname: jest.fn() }))

const links = [
  { href: "/", label: "Home", translationKey: "nav.home" },
  { href: "/opac", label: "E-Book", translationKey: "nav.ebooks" },
  { href: "/catalogue", label: "Catalogue", translationKey: "nav.catalogue" },
  { href: "/archive", label: "Archive", translationKey: "nav.archive" },
  { href: "/membership", label: "Membership", translationKey: "nav.membership" },
  { href: "/about", label: "About", translationKey: "nav.about" },
]

function renderHeader(pathname: string) {
  const { usePathname } = jest.requireMock("next/navigation") as {
    usePathname: jest.Mock
  }
  usePathname.mockReturnValue(pathname)
  return render(
    <LanguageProvider>
      <SiteHeader links={links} />
    </LanguageProvider>
  )
}

test("shows public navigation and highlights the active page", () => {
  renderHeader("/opac")

  for (const label of ["Home", "E-Book", "Catalogue", "Archive", "Membership", "About"]) {
    expect(screen.getByRole("link", { name: label })).toBeInTheDocument()
  }
  expect(screen.getByRole("link", { name: "E-Book" })).toHaveAttribute("aria-current", "page")
  expect(screen.getByRole("link", { name: "Catalogue" })).toHaveAttribute("href", "/catalogue")
  expect(screen.queryByRole("link", { name: "Administration" })).not.toBeInTheDocument()
  expect(screen.getByRole("link", { name: "Facebook" })).toHaveAttribute("target", "_blank")
  expect(screen.getByText("IQQO Digital Library")).toBeInTheDocument()
  expect(screen.getByText("Oromia Institution of Studies and Research")).toBeInTheDocument()
  expect(screen.getByRole("img", { name: "IQQO Digital Library logo" })).toBeInTheDocument()
})

test("highlights the catalogue link on the catalogue page", () => {
  renderHeader("/catalogue")

  expect(screen.getByRole("link", { name: "Catalogue" })).toHaveAttribute("aria-current", "page")
  expect(screen.queryByRole("link", { name: "E-Book" })).not.toHaveAttribute("aria-current")
})

test("language selection and mobile menu are keyboard accessible", () => {
  renderHeader("/")

  const language = screen.getByLabelText("Language")
  expect(language).toHaveValue("en")
  fireEvent.change(language, { target: { value: "om" } })
  expect(language).toHaveValue("om")
  expect(screen.getByRole("link", { name: "Kitaboo Elektroonikaa" })).toBeInTheDocument()

  const toggle = screen.getByRole("button", { name: "Menu" })
  expect(toggle).toHaveAttribute("aria-expanded", "false")
  fireEvent.click(toggle)
  expect(toggle).toHaveAttribute("aria-expanded", "true")
  expect(screen.getByRole("navigation", { name: "Public" })).toHaveClass("site-nav--open")
})
