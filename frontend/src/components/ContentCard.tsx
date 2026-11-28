"use client"

import Link from "next/link"
import { Icon } from "@/components/Icon"
import { useLanguage } from "@/context/LanguageContext"
import type { LocalizedCard } from "@/lib/website"

export function ContentCard({ card, compact = false }: { card: LocalizedCard; compact?: boolean }) {
  const { t } = useLanguage()
  return (
    <article className={`content-card${compact ? " content-card--compact" : ""}`}>
      <span className="content-card-icon">
        <Icon name={card.icon} width={26} height={26} />
      </span>
      <h3>{card.title}</h3>
      {card.description ? <p>{card.description}</p> : null}
      {card.linkPath ? (
        <Link className="text-link" href={card.linkPath}>
          {card.linkLabel || t("card.viewDetails")}
          <Icon name="arrow" width={16} height={16} />
        </Link>
      ) : null}
    </article>
  )
}
