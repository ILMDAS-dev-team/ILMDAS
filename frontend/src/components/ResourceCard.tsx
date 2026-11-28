"use client"

import Image from "next/image"
import Link from "next/link"
import { Icon } from "@/components/Icon"
import { useLanguage } from "@/context/LanguageContext"
import type { FeaturedResource } from "@/lib/website"

function typeLabel(type: string): string {
  return type
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ")
}

export function ResourceCard({ resource }: { resource: FeaturedResource }) {
  const { t } = useLanguage()
  const label = typeLabel(resource.resourceType)

  return (
    <article className="resource-card">
      <div className="resource-card-media">
        {resource.thumbnailPath ? (
          <Image
            src={resource.thumbnailPath}
            alt=""
            fill
            sizes="(max-width: 640px) 100vw, (max-width: 1100px) 50vw, 20vw"
            style={{ objectFit: "cover" }}
          />
        ) : (
          <div className="resource-card-placeholder">
            <Icon
              name={resource.resourceType === "audio" ? "audio" : "book"}
              width={34}
              height={34}
            />
            <span>{label}</span>
          </div>
        )}
        <span className="resource-card-badge">{label}</span>
      </div>
      <div className="resource-card-body">
        <h3>{resource.title}</h3>
        {resource.description ? <p>{resource.description}</p> : null}
        <p className="resource-card-status">
          {resource.accessStatus === "restricted"
            ? t("card.access.restricted")
            : t("card.access.public")}
        </p>
        <Link className="button button--dark button--full" href={resource.detailPath}>
          {t("card.viewDetails")}
        </Link>
      </div>
    </article>
  )
}
