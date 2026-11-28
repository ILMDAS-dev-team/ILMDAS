import { render, screen } from "@testing-library/react"
import { SocialLinks } from "@/components/SocialLinks"

const links = [
  { label: "YouTube", url: "https://www.youtube.com/ilmdas", icon: "youtube" },
  { label: "Facebook", url: "https://www.facebook.com/ilmdas", icon: "facebook" },
  { label: "Instagram", url: "https://www.instagram.com/ilmdas", icon: "instagram" },
  { label: "Telegram", url: "https://t.me/ilmdas", icon: "telegram" },
  { label: "TikTok", url: "https://www.tiktok.com/@ilmdas", icon: "tiktok" },
  { label: "LinkedIn", url: "https://www.linkedin.com/company/ilmdas", icon: "linkedin" },
  { label: "Newsletter", url: "https://example.org/newsletter", icon: "" },
  { label: "Unconfigured", url: "", icon: "facebook" },
]

test("renders only approved social platforms with safe external links", () => {
  render(<SocialLinks links={links} />)

  expect(screen.getByRole("list", { name: "Social media" })).toBeInTheDocument()
  for (const label of ["YouTube", "Facebook", "Instagram", "Telegram", "TikTok", "LinkedIn"]) {
    const link = screen.getByRole("link", { name: label })
    expect(link).toHaveAttribute("target", "_blank")
    expect(link).toHaveAttribute("rel", "noopener noreferrer")
    expect(link.querySelector("svg")).toHaveAttribute("aria-hidden", "true")
  }
  expect(screen.queryByRole("link", { name: "Newsletter" })).not.toBeInTheDocument()
  expect(screen.queryByRole("link", { name: "Unconfigured" })).not.toBeInTheDocument()
})

test("renders nothing when no social footer rows are approved", () => {
  const { container } = render(<SocialLinks links={[]} />)
  expect(container).toBeEmptyDOMElement()
})
