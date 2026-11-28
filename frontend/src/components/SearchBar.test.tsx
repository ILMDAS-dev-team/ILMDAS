import { render, screen } from "@testing-library/react"
import { LanguageProvider } from "@/context/LanguageContext"
import { SearchBar } from "@/components/SearchBar"

function renderSearchBar() {
  return render(
    <LanguageProvider>
      <SearchBar
        label="SEARCH THE LIBRARY & ARCHIVE"
        placeholder="Title, author, subject or keyword"
        buttonLabel="Search"
        popularSearches={[{ label: "Afaan Oromo", query: "Afaan Oromo" }]}
        category="ebooks"
      />
    </LanguageProvider>
  )
}

test("search submits to the existing OPAC route with a category filter", () => {
  renderSearchBar()
  const form = screen.getByRole("search")

  expect(form).toHaveAttribute("action", "/opac")
  expect(form).toHaveAttribute("method", "get")
  expect(screen.getByPlaceholderText("Title, author, subject or keyword")).toHaveAttribute(
    "name",
    "q"
  )
  expect(document.querySelector('input[name="category"]')).toHaveValue("ebooks")
})

test("popular suggestions link to OPAC searches", () => {
  renderSearchBar()
  expect(screen.getByRole("link", { name: "Afaan Oromo" })).toHaveAttribute(
    "href",
    "/opac?q=Afaan%20Oromo"
  )
})
