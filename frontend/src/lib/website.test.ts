import { apiFetch } from "@/lib/api"
import { fetchHomepage } from "@/lib/website"

jest.mock("@/lib/api", () => ({
  ...jest.requireActual("@/lib/api"),
  apiFetch: jest.fn(),
}))

const mockedApiFetch = apiFetch as jest.Mock

beforeEach(() => {
  mockedApiFetch.mockReset()
})

test("fetchHomepage uses the public endpoint and requested language", async () => {
  const payload = {
    language: "om",
    hero: {},
    offers: { title: "", subtitle: "", cards: [] },
    footer: { description: "", groups: {} },
    categories: [],
  }
  mockedApiFetch.mockResolvedValue({
    response: { ok: true, json: async () => payload },
  })

  await expect(fetchHomepage("om")).resolves.toEqual(payload)
  expect(mockedApiFetch).toHaveBeenCalledWith("/api/v1/website/home/?lang=om")
})

test("fetchHomepage reports an unsuccessful response", async () => {
  mockedApiFetch.mockResolvedValue({ response: { ok: false, status: 503 } })
  await expect(fetchHomepage("en")).rejects.toThrow("Failed to fetch homepage: 503")
})
