"use client"

import Image from "next/image"
import { useEffect, useRef, useState } from "react"
import { heroSlideshowImages } from "@/lib/homeImages"

/** Full-width hero slideshow of homepage pictures. */
export function HeroSlideshow() {
  const [activeIndex, setActiveIndex] = useState(0)
  const [paused, setPaused] = useState(false)
  const timerRef = useRef<number | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const slides = heroSlideshowImages

  useEffect(() => {
    if (typeof window === "undefined") return

    const handleMouseEnter = () => setPaused(true)
    const handleMouseLeave = () => setPaused(false)

    const container = containerRef.current
    container?.addEventListener("mouseenter", handleMouseEnter)
    container?.addEventListener("mouseleave", handleMouseLeave)

    if (!paused) {
      timerRef.current = window.setInterval(() => {
        setActiveIndex((index) => (index + 1) % slides.length)
      }, 6000)
    }

    return () => {
      container?.removeEventListener("mouseenter", handleMouseEnter)
      container?.removeEventListener("mouseleave", handleMouseLeave)
      if (timerRef.current !== null) {
        window.clearInterval(timerRef.current)
      }
    }
  }, [paused, slides.length])

  return (
    <div
      ref={containerRef}
      className="hero-slideshow"
      aria-label="Hero picture slideshow"
      role="region"
      aria-roledescription="slideshow"
    >
      {slides.map((slide, index) => (
        <div
          key={slide.key}
          className={`hero-slide${index === activeIndex ? " hero-slide--active" : ""}`}
          aria-hidden={index !== activeIndex}
        >
          <Image
            className="hero-slide-backdrop"
            src={slide.src}
            alt=""
            fill
            priority={index === activeIndex}
            sizes="100vw"
            style={{ objectFit: "cover", objectPosition: "center" }}
          />
          <Image
            className="hero-slide-image"
            src={slide.src}
            alt=""
            fill
            priority={index === activeIndex}
            sizes="100vw"
            style={{ objectFit: "contain", objectPosition: "center" }}
          />
        </div>
      ))}
      <button
        className="hero-slide-prev"
        type="button"
        onClick={() => setActiveIndex((index) => (index - 1 + slides.length) % slides.length)}
        aria-label="Previous hero picture"
      >
        <span className="visually-hidden">Previous</span>
        <span aria-hidden="true">‹</span>
      </button>
      <button
        className="hero-slide-next"
        type="button"
        onClick={() => setActiveIndex((index) => (index + 1) % slides.length)}
        aria-label="Next hero picture"
      >
        <span className="visually-hidden">Next</span>
        <span aria-hidden="true">›</span>
      </button>
      <ol className="hero-slide-pagination" aria-label="Hero picture slides">
        {slides.map((_, index) => (
          <li key={index}>
            <button
              className={index === activeIndex ? "hero-slide-pagination--active" : ""}
              onClick={() => setActiveIndex(index)}
              aria-label={`Slide ${index + 1} of ${slides.length}`}
              aria-pressed={index === activeIndex}
            />
          </li>
        ))}
      </ol>
    </div>
  )
}
