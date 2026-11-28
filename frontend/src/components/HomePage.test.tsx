import { render, screen, waitFor } from "@testing-library/react"
import { HomePage } from "@/components/HomePage"
import { LanguageProvider } from "@/context/LanguageContext"
import { WebsiteProvider } from "@/context/WebsiteContext"
import { apiFetch } from "@/lib/api"
import { fallbackHomepage } from "@/lib/homepageContent"
import type { HomepagePayload } from "@/lib/website"

jest.mock("@/lib/api", () => ({
  ...jest.requireActual("@/lib/api"),
  apiFetch: jest.fn(),
}))

const mockedApiFetch = apiFetch as jest.Mock

function renderHome(payload: HomepagePayload = fallbackHomepage("en"), fail = false) {
  mockedApiFetch.mockImplementation(() =>
    fail
      ? Promise.reject(new Error("offline"))
      : Promise.resolve({ response: { ok: true, json: async () => payload } })
  )
  return render(
    <LanguageProvider>
      <WebsiteProvider>
        <HomePage />
      </WebsiteProvider>
    </LanguageProvider>
  )
}

async function waitForReady() {
  await waitFor(() => {
    expect(screen.queryByRole("status")).not.toBeInTheDocument()
  })
}

const publicResource = {
  id: 1,
  title: "Oral History Collection",
  resourceType: "oral_history",
  source: "archive",
  sourceId: "archive-1",
  description: "Voices from Oromo communities.",
  detailPath: "/archive/archive-1/",
  thumbnailPath: "",
  accessStatus: "public",
}

beforeEach(() => {
  mockedApiFetch.mockReset()
})

test("renders the hero, discovery sections and membership call to action", async () => {
  renderHome()
  await waitForReady()

  expect(
    screen.getByRole("heading", { name: "A world of knowledge. A heritage to keep." })
  ).toBeInTheDocument()
  expect(screen.getAllByRole("search")).toHaveLength(1)
  expect(screen.getByRole("region", { name: /hero picture slideshow/i })).toBeInTheDocument()
  expect(screen.getByRole("heading", { name: "What We Offer" })).toBeInTheDocument()
  expect(screen.getByRole("heading", { name: "Explore Our Collection" })).toBeInTheDocument()
  expect(screen.getByRole("heading", { name: "Heritage & Digital Archive" })).toBeInTheDocument()
  expect(screen.getByRole("heading", { name: "E-Books" })).toBeInTheDocument()
  expect(screen.getByRole("heading", { name: "From ILMDAS" })).toBeInTheDocument()
  expect(screen.getByRole("heading", { name: "Become a Member" })).toBeInTheDocument()
  expect(screen.getByRole("link", { name: /Explore membership/ })).toHaveAttribute(
    "href",
    "/membership"
  )
})

test("shows only public featured resources and approved updates", async () => {
  const payload: HomepagePayload = {
    ...fallbackHomepage("en"),
    featuredResources: [
      publicResource,
      { ...publicResource, id: 2, title: "Restricted Record", accessStatus: "restricted" },
    ],
    updates: [
      {
        id: 9,
        kind: "announcement",
        title: "Approved announcement",
        summary: "An update from ILMDAS.",
        detailPath: "/about/announcement-9/",
        imagePath: "",
        publishedAt: "2026-01-01T00:00:00Z",
        eventDate: null,
      },
    ],
  }
  renderHome(payload)
  await waitForReady()

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: "Oral History Collection" })).toBeInTheDocument()
  })
  expect(screen.queryByText("Restricted Record")).not.toBeInTheDocument()
  expect(screen.getByRole("heading", { name: "Approved announcement" })).toBeInTheDocument()
})

test("keeps the usable shell when the API is unavailable", async () => {
  renderHome(undefined, true)

  await waitFor(() => {
    expect(screen.getByRole("status")).toHaveTextContent("temporarily unavailable")
  })
  expect(
    screen.getByRole("heading", { name: "A world of knowledge. A heritage to keep." })
  ).toBeInTheDocument()
})
