import { Icon } from "@/components/Icon"
import { isSocialIcon } from "@/lib/socialPlatforms"
import type { FooterLink } from "@/lib/website"

/** Social icons are driven only by approved backend footer rows. */
export function SocialLinks({
  links,
  className = "",
}: {
  links: FooterLink[]
  className?: string
}) {
  const socialLinks = links.filter((link) => link.url?.trim() && isSocialIcon(link.icon))
  if (socialLinks.length === 0) return null

  const classes = ["social-links", className].filter(Boolean).join(" ")

  return (
    <ul className={classes} aria-label="Social media">
      {socialLinks.map((link) => (
        <li key={`${link.url}-${link.label}`}>
          <a
            href={link.url}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={link.label}
            title={link.label}
          >
            <Icon name={link.icon.toLowerCase()} width={18} height={18} />
          </a>
        </li>
      ))}
    </ul>
  )
}
