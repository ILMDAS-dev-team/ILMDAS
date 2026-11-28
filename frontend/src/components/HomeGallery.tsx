"use client"

import Image from "next/image"
import { SectionHeading } from "@/components/SectionHeading"
import { useLanguage } from "@/context/LanguageContext"
import { homeGalleryImages } from "@/lib/homeImages"

export function HomeGallery() {
  const { t } = useLanguage()

  return (
    <section className="home-section" aria-labelledby="gallery-title">
      <SectionHeading
        id="gallery-title"
        title={t("gallery.title")}
        subtitle={t("gallery.subtitle")}
      />
      <div className="gallery-grid">
        {homeGalleryImages.map((image) => (
          <figure className="gallery-item" key={image.key}>
            <div className="gallery-item-media">
              <Image
                src={image.src}
                alt={t(image.altKey)}
                fill
                sizes="(max-width: 640px) 100vw, (max-width: 1100px) 50vw, 25vw"
                style={{ objectFit: "cover" }}
              />
            </div>
            <figcaption>{t(image.captionKey)}</figcaption>
          </figure>
        ))}
      </div>
    </section>
  )
}
