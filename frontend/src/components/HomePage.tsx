"use client"

import Link from "next/link"
import { CategoryList } from "@/components/CategoryList"
import { ContentCard } from "@/components/ContentCard"
import { HeroSlideshow } from "@/components/HeroSlideshow"
import { HomeGallery } from "@/components/HomeGallery"
import { Icon } from "@/components/Icon"
import { ResourceCard } from "@/components/ResourceCard"
import { SearchBar } from "@/components/SearchBar"
import { SectionHeading } from "@/components/SectionHeading"
import { UpdateCard } from "@/components/UpdateCard"
import { useLanguage } from "@/context/LanguageContext"
import { useWebsite } from "@/context/WebsiteContext"

export function HomePage() {
  const { t } = useLanguage()
  const { homepage, status } = useWebsite()
  const featured = homepage.featuredResources.filter(
    (resource) => resource.accessStatus !== "restricted"
  )

  return (
    <>
      <section className="hero-section" aria-labelledby="hero-title">
        <div className="hero-panel">
          <HeroSlideshow />
          <div className="hero-copy">
            <p className="eyebrow-group eyebrow-group--full">
              {String(homepage.hero.eyebrow)
                .split("·")
                .map((item) => item.trim())
                .filter(Boolean)
                .map((item) => (
                  <span key={item}>{item}</span>
                ))}
            </p>
            <h1 id="hero-title">{homepage.hero.title}</h1>
            <p className="hero-description">{homepage.hero.description}</p>
          </div>
        </div>
      </section>

      {status === "error" ? (
        <p className="content-status" role="status">
          {t("state.error")}
        </p>
      ) : null}
      {status === "loading" ? (
        <p className="visually-hidden" role="status">
          {t("state.loading")}
        </p>
      ) : null}

      <section className="home-section" aria-labelledby="offers-title">
        <SectionHeading
          id="offers-title"
          title={homepage.offers.title}
          subtitle={homepage.offers.subtitle}
        />
        <div className="card-grid card-grid--three">
          {homepage.offers.cards.map((card, index) => (
            <ContentCard key={`${card.title}-${index}`} card={card} />
          ))}
        </div>
      </section>

      <section className="home-section home-section--tint" aria-labelledby="collection-title">
        <SectionHeading
          id="collection-title"
          title={t("section.collection.title")}
          subtitle={t("section.collection.subtitle")}
        />
        <SearchBar
          label={t("section.collection.searchPlaceholder")}
          placeholder={t("section.collection.searchPlaceholder")}
          buttonLabel={t("hero.searchButton")}
          variant="section"
        />
        <h3 className="subheading">{t("section.collection.all")}</h3>
        <CategoryList categories={homepage.categories} />

        <div className="featured-header">
          <SectionHeading
            id="featured-title"
            title={t("section.featured.title")}
            subtitle={t("section.featured.subtitle")}
          />
          <Link className="text-link" href="/opac">
            {t("section.collection.all")}
            <Icon name="arrow" width={16} height={16} />
          </Link>
        </div>
        {featured.length > 0 ? (
          <div className="card-grid card-grid--featured">
            {featured.map((resource, index) => (
              <ResourceCard key={`${resource.sourceId}-${index}`} resource={resource} />
            ))}
          </div>
        ) : (
          <p className="empty-state">{t("state.noFeatured")}</p>
        )}
      </section>

      <section className="heritage-section" aria-labelledby="heritage-title">
        <div className="heritage-intro">
          <span className="section-kicker">{t("section.heritage.title")}</span>
          <h2 id="heritage-title">{homepage.heritage.title}</h2>
          <p>{homepage.heritage.subtitle}</p>
        </div>
        <div className="card-grid card-grid--heritage">
          {homepage.heritage.cards.map((card, index) => (
            <ContentCard key={`${card.title}-${index}`} card={card} compact />
          ))}
        </div>
      </section>

      <HomeGallery />

      <section className="home-section" aria-labelledby="learning-title">
        <SectionHeading
          id="learning-title"
          title={homepage.learning.title}
          subtitle={homepage.learning.subtitle}
        />
        <div className="card-grid card-grid--three">
          {homepage.learning.cards.map((card, index) => (
            <ContentCard key={`${card.title}-${index}`} card={card} />
          ))}
        </div>
      </section>

      {homepage.updates.length > 0 ? (
        <section className="home-section home-section--tint" aria-labelledby="updates-title">
          <SectionHeading
            id="updates-title"
            title={t("section.events.title")}
            subtitle={t("section.events.subtitle")}
          />
          <div className="card-grid card-grid--three">
            {homepage.updates.map((update) => (
              <UpdateCard key={update.id || update.title} update={update} />
            ))}
          </div>
        </section>
      ) : null}

      <section className="membership-section" aria-labelledby="membership-title">
        <div>
          <span className="section-kicker">ILMDAS</span>
          <h2 id="membership-title">{homepage.membership.title}</h2>
          <p>{homepage.membership.description}</p>
        </div>
        <Link className="button button--gold" href={homepage.membership.path || "/membership"}>
          {t("section.membership.cta")}
          <Icon name="arrow" width={18} height={18} />
        </Link>
      </section>
    </>
  )
}
