/** Social destinations shown in the public header and footer. */

export type SocialLink = {
  label: string
  icon: string
  href: string
}

/** Replace the NEXT_PUBLIC_ILMDAS_* values with verified ILMDAS account URLs. */
function destination(value: string | undefined, fallback: string): string {
  return value?.trim() || fallback
}

export const socialLinks: SocialLink[] = [
  {
    label: "Facebook",
    icon: "facebook",
    href: destination(process.env.NEXT_PUBLIC_ILMDAS_FACEBOOK_URL, "https://www.facebook.com/"),
  },
  {
    label: "YouTube",
    icon: "youtube",
    href: destination(process.env.NEXT_PUBLIC_ILMDAS_YOUTUBE_URL, "https://www.youtube.com/"),
  },
  {
    label: "Instagram",
    icon: "instagram",
    href: destination(process.env.NEXT_PUBLIC_ILMDAS_INSTAGRAM_URL, "https://www.instagram.com/"),
  },
  {
    label: "X",
    icon: "x",
    href: destination(process.env.NEXT_PUBLIC_ILMDAS_X_URL, "https://x.com/"),
  },
]
