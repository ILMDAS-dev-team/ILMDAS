import type { SVGProps } from "react"

/** Small inline icons so cards need no image assets or icon dependency. */
const paths: Record<string, string> = {
  book: "M4 5.5A2.5 2.5 0 0 1 6.5 3H19v16H6.5A2.5 2.5 0 0 0 4 21V5.5Zm0 0V21",
  digital: "M4 7h16v11H4V7Zm3 11v2m10-2v2M8 11h8M8 14h5",
  research:
    "M10 4a6 6 0 1 0 3.5 10.9L20 21l1.5-1.5-6.6-6.5A6 6 0 0 0 10 4Zm0 2.5a3.5 3.5 0 1 1 0 7 3.5 3.5 0 0 1 0-7Z",
  archive: "M3 6h18v4H3V6Zm2 4v10h14V10M9 13h6",
  layers: "M12 3 3 8l9 5 9-5-9-5Zm-9 9 9 5 9-5M3 16l9 5 9-5",
  community:
    "M8 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm8 0a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM2 20c0-3.3 2.7-5 6-5s6 1.7 6 5m0-5c3.3 0 6 1.7 6 5",
  search:
    "M10 4a6 6 0 1 0 3.5 10.9L20 21l1.5-1.5-6.6-6.5A6 6 0 0 0 10 4Zm0 2.5a3.5 3.5 0 1 1 0 7 3.5 3.5 0 0 1 0-7Z",
  play: "M4 5h16v14H4V5Zm5 3 8 4-8 4V8Z",
  audio: "M5 14v-4m4 7V7m4 12V5m4 12V9m4 6v-4",
  menu: "M4 7h16M4 12h16M4 17h16",
  close: "M5 5l14 14M19 5 5 19",
  arrow: "M5 12h14m-6-6 6 6-6 6",
  up: "M12 19V5m-6 6 6-6 6 6",
  facebook: "M14 8h3V5h-3a4 4 0 0 0-4 4v3H8v3h2.5V21H14v-7h3l.8-3H14V9a1 1 0 0 1 1-1Z",
  youtube: "M3 8a3 3 0 0 1 3-3h12a3 3 0 0 1 3 3v8a3 3 0 0 1-3 3H6a3 3 0 0 1-3-3V8Zm6 0 7 4-7 4V8Z",
  instagram:
    "M4 8a4 4 0 0 1 4-4h8a4 4 0 0 1 4 4v8a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4V8Zm4 0h8v8H8V8Zm8-1h.01",
  telegram: "M21 4 3 11l6 2.5L12 21l3-7 6-10ZM9 13.5 21 4",
  tiktok:
    "M14 3v11.5a4.5 4.5 0 1 1-4.5-4.5c.5 0 1 .08 1.5.23V6.7A7 7 0 1 0 17 13V8.2a6 6 0 0 0 4 1.3V6a4 4 0 0 1-4-4h-3Z",
  linkedin: "M6 9v10M6 6.5v.01M11 19V9m0 3a3 3 0 0 1 6 0v7M11 13v6",
}

export function Icon({ name, ...props }: { name: string } & SVGProps<SVGSVGElement>) {
  const path = paths[name] ?? paths.layers
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d={path} />
    </svg>
  )
}
