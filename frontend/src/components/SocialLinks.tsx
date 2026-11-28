import { Icon } from "@/components/Icon"
import { socialLinks } from "@/lib/socialLinks"

export function SocialLinks({ className = "" }: { className?: string }) {
  const classes = ["social-links", className].filter(Boolean).join(" ")

  return (
    <ul className={classes} aria-label="Social media">
      {socialLinks.map((link) => (
        <li key={link.label}>
          <a
            href={link.href}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={link.label}
            title={link.label}
          >
            <Icon name={link.icon} width={18} height={18} />
          </a>
        </li>
      ))}
    </ul>
  )
}
