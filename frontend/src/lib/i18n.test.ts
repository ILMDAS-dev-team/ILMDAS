import { isLanguageCode, LANGUAGE_CODES, translate } from "@/lib/i18n"

test("all ILMDAS languages have the core navigation labels", () => {
  for (const language of LANGUAGE_CODES) {
    expect(translate(language, "nav.home")).not.toBe("")
    expect(translate(language, "hero.title")).not.toBe("")
    expect(translate(language, "nav.home")).not.toBe("nav.home")
    expect(translate(language, "card.readMore")).not.toBe("card.readMore")
    expect(translate(language, "nav.backToTop")).not.toBe("nav.backToTop")
    expect(translate(language, "nav.ebooks")).not.toBe("nav.ebooks")
    expect(translate(language, "nav.catalogue")).not.toBe("nav.catalogue")
    expect(translate(language, "catalogue.searchLabel")).not.toBe("catalogue.searchLabel")
    expect(translate(language, "gallery.title")).not.toBe("gallery.title")
  }
})

test("unknown keys and codes fall back safely", () => {
  expect(translate("om", "missing.key")).toBe("missing.key")
  expect(isLanguageCode("om")).toBe(true)
  expect(isLanguageCode("zz")).toBe(false)
  expect(isLanguageCode(undefined)).toBe(false)
})
