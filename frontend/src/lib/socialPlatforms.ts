/** Social platforms required by FR-WEB-003; destinations come from managed footer rows. */

export const SOCIAL_ICONS = [
  "youtube",
  "facebook",
  "instagram",
  "telegram",
  "tiktok",
  "linkedin",
] as const

export type SocialIcon = (typeof SOCIAL_ICONS)[number]

export function isSocialIcon(icon: string): icon is SocialIcon {
  return (SOCIAL_ICONS as readonly string[]).includes(icon.toLowerCase())
}
