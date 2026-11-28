import { render, screen } from "@testing-library/react"
import { SocialLinks } from "@/components/SocialLinks"

test("renders accessible social links that open safely in a new tab", () => {
  render(<SocialLinks />)

  expect(screen.getByRole("list", { name: "Social media" })).toBeInTheDocument()
  for (const label of ["Facebook", "YouTube", "Instagram", "X"]) {
    const link = screen.getByRole("link", { name: label })
    expect(link).toHaveAttribute("target", "_blank")
    expect(link).toHaveAttribute("rel", "noopener noreferrer")
    expect(link.querySelector("svg")).toHaveAttribute("aria-hidden", "true")
  }
})
