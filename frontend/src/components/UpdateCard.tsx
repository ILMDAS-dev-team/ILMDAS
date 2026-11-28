"use client"

import Link from "next/link"
import { useLanguage } from "@/context/LanguageContext"
import type { InstitutionalUpdate } from "@/lib/website"

export function UpdateCard({ update }: { update: InstitutionalUpdate }) {
  const { t } = useLanguage()
  const translatedKind = t(`update.kind.${update.kind}`)
  const kindLabel = translatedKind.startsWith("update.kind.")
    ? update.kind.replace(/_/g, " ")
    : translatedKind

  return (
    <article className="update-card">
      <span className="event-tag">{kindLabel}</span>
      <h3>{update.title}</h3>
      {update.summary ? <p>{update.summary}</p> : null}
      <time dateTime={update.eventDate || update.publishedAt}>
        {(update.eventDate || update.publishedAt).slice(0, 10)}
      </time>
      {update.detailPath ? (
        <Link className="text-link" href={update.detailPath}>
          {t("card.readMore")}
        </Link>
      ) : null}
    </article>
  )
}
