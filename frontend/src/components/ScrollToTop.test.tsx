import { fireEvent, render, screen } from "@testing-library/react"
import { ScrollToTop } from "@/components/ScrollToTop"
import { LanguageProvider } from "@/context/LanguageContext"

function setScrollY(value: number) {
  Object.defineProperty(window, "scrollY", { configurable: true, writable: true, value })
}

beforeEach(() => {
  setScrollY(0)
  Object.defineProperty(window, "scrollTo", {
    configurable: true,
    writable: true,
    value: jest.fn(),
  })
})

test("appears after scrolling and returns the visitor to the top", () => {
  render(
    <LanguageProvider>
      <ScrollToTop />
    </LanguageProvider>
  )

  expect(screen.queryByRole("button", { name: "Back to top" })).not.toBeInTheDocument()

  setScrollY(600)
  fireEvent.scroll(window)

  const button = screen.getByRole("button", { name: "Back to top" })
  fireEvent.click(button)

  expect(window.scrollTo).toHaveBeenCalledWith({ top: 0, behavior: "smooth" })
})

test("hides again when the visitor returns to the top", () => {
  render(
    <LanguageProvider>
      <ScrollToTop />
    </LanguageProvider>
  )

  setScrollY(600)
  fireEvent.scroll(window)
  expect(screen.getByRole("button", { name: "Back to top" })).toBeInTheDocument()

  setScrollY(0)
  fireEvent.scroll(window)
  expect(screen.queryByRole("button", { name: "Back to top" })).not.toBeInTheDocument()
})
