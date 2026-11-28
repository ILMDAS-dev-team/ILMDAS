# Public homepage content

The public homepage is served by the `apps.homepage` Django app. Content teams manage it through
the admin or the role-guarded management endpoints; the Next.js public shell reads the anonymous
endpoint only.

## Public endpoint

```http
GET /api/v1/website/home/?lang=en|om|am
```

- `lang` accepts `en`, `om` and `am`. Unknown values fall back to `en`.
- The response is read-only and requires no authentication.
- Only approved rows are returned:
  - `is_published` / `is_approved` must be true.
  - Scheduled updates with a future `published_at` are excluded.
  - Featured resources with `access="restricted"` are excluded.
- Featured resources and institutional updates are limited to the latest six rows each.
- Only one `Homepage` row may be published at a time. The management serializer returns a 400
  validation error for a second published row, and a partial unique constraint in the database
  protects against concurrent writes. Unpublish the current row before publishing another one.

The payload contains `hero`, `offers`, `heritage`, `learning`, `categories`, `featuredResources`,
`updates`, `membership` and `footer` sections. Missing translations fall back to the base field.

## Footer social links (FR-WEB-003)

Social icons are not hard-coded and do not use environment variables. The footer renders icons from
approved `FooterLink` rows in the `connect` group. Set `icon` to one of these platform names:

| Platform | Icon value |
|---|---|
| YouTube | `youtube` |
| Facebook | `facebook` |
| Instagram | `instagram` |
| Telegram | `telegram` |
| TikTok | `tiktok` |
| LinkedIn | `linkedin` |

Rows with no configured URL are not rendered. A row that uses a recognised social icon appears as an
icon in the footer brand area and is excluded from the text Connect column, so both views come from
the same managed row.

## Featured resource access

`FeaturedResource.access` is currently curated manually. Publishing a row marks its metadata as
publicly visible, so the content owner must confirm the access level of the referenced catalogue or
archive record before setting `access="public"` and `is_published=true`. Downloads remain protected
by the owning apps, but titles, summaries and thumbnails would still be public if a row were marked
incorrectly. Remove manual check once the catalogue and archive apps expose machine-readable access
levels.

## Image provenance

The local homepage photographs were renamed from generic downloads to descriptive filenames:

| Previous name | Current name |
|---|---|
| `images (2).jpeg` | `library-and-archive.jpeg` |
| `images.jpeg` | `collection-highlights.jpeg` |
| `images (1).jpeg` | `community-knowledge.jpeg` |
| `oromo-irreechaa-thanks-giving-festival.webp` | `irreechaa-festival.webp` |

Ownership or licence is **not verified** by this change. The content owner must confirm IQQO owns or
has a licence for each photograph before production deployment; provenance is not recorded in this
repository.
