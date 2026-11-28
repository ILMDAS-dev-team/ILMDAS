import { render, screen, waitFor } from "@testing-library/react"
import { SiteFooter } from "@/components/SiteFooter"
import { LanguageProvider } from "@/context/LanguageContext"
import { WebsiteProvider } from "@/context/WebsiteContext"
import { apiFetch } from "@/lib/api"
import { fallbackHomepage } from "@/lib/homepageContent"

jest.mock("@/lib/api", () => ({
  ...jest.requireActual("@/lib/api"),
  apiFetch: jest.fn(),
}))

const mockedApiFetch = apiFetch as jest.Mock

beforeEach(() => {
  mockedApiFetch.mockReset()
})

function renderFooter(groups?: Record<string, { label: string; url: string; icon: string }[]>) {
  const payload = {
    ...fallbackHomepage("en"),
    footer: {
      description: "Approved institutional description.",
      groups: groups ?? fallbackHomepage("en").footer.groups,
    },
  }
  mockedApiFetch.mockResolvedValue({
    response: { ok: true, json: async () => payload },
  })
  return render(
    <LanguageProvider>
      <WebsiteProvider>
        <SiteFooter />
      </WebsiteProvider>
    </LanguageProvider>
  )
}

test("footer shows branding and approved navigation", async () => {
  renderFooter({
    quick_links: [{ label: "About", url: "/about", icon: "" }],
    connect: [
      { label: "YouTube", url: "https://www.youtube.com/ilmdas", icon: "youtube" },
      { label: "ILMDAS channel", url: "https://example.org", icon: "" },
    ],
  })

  expect(screen.getByRole("contentinfo")).toBeInTheDocument()
  expect(screen.getByText("IQQO Digital Library")).toBeInTheDocument()
  expect(screen.getByText("Oromia Institution of Studies and Research")).toBeInTheDocument()
  await waitFor(() => {
    expect(screen.getByText("Approved institutional description.")).toBeInTheDocument()
  })
  expect(screen.getAllByRole("link", { name: "YouTube" })).toHaveLength(1)
  expect(screen.getByRole("link", { name: "YouTube" })).toHaveAttribute("target", "_blank")
  expect(screen.getByRole("link", { name: "About" })).toHaveAttribute("href", "/about")
  const external = screen.getByRole("link", { name: "ILMDAS channel" })
  expect(external).toHaveAttribute("target", "_blank")
  expect(external).toHaveAttribute("rel", "noopener noreferrer")
})
