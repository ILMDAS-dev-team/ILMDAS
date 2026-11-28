import { fireEvent, render, screen } from "@testing-library/react"
import { HeroSlideshow } from "@/components/HeroSlideshow"

test("renders picture slides with accessible controls", () => {
  render(<HeroSlideshow />)

  expect(screen.getByRole("region", { name: /hero picture slideshow/i })).toBeInTheDocument()
  expect(screen.getByRole("button", { name: "Previous hero picture" })).toBeInTheDocument()
  expect(screen.getByRole("button", { name: "Next hero picture" })).toBeInTheDocument()
  expect(screen.getByRole("button", { name: "Slide 1 of 4" })).toBeInTheDocument()
  expect(screen.getByRole("button", { name: "Slide 4 of 4" })).toBeInTheDocument()
})

test("keeps each hero picture whole inside a filled backdrop", () => {
  const { container } = render(<HeroSlideshow />)
  const activeSlide = container.querySelector(".hero-slide--active")

  expect(activeSlide?.querySelector(".hero-slide-backdrop")).toHaveStyle("object-fit: cover")
  expect(activeSlide?.querySelector(".hero-slide-image")).toHaveStyle("object-fit: contain")
})

test("starts on the first slide and advances with controls", () => {
  render(<HeroSlideshow />)

  expect(screen.getByRole("button", { name: "Slide 1 of 4" })).toHaveAttribute(
    "aria-pressed",
    "true"
  )
  expect(screen.queryByRole("button", { name: "Slide 2 of 4" })).not.toHaveAttribute(
    "aria-pressed",
    "true"
  )

  fireEvent.click(screen.getByRole("button", { name: "Next hero picture" }))
  expect(screen.getByRole("button", { name: "Slide 2 of 4" })).toHaveAttribute(
    "aria-pressed",
    "true"
  )

  fireEvent.click(screen.getByRole("button", { name: "Slide 4 of 4" }))
  expect(screen.getByRole("button", { name: "Slide 4 of 4" })).toHaveAttribute(
    "aria-pressed",
    "true"
  )
})
