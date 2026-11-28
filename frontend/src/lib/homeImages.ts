/** Local homepage images supplied in `frontend/Images`. */

import collectionImage from "../../Images/images.jpeg"
import communityImage from "../../Images/images (1).jpeg"
import libraryImage from "../../Images/images (2).jpeg"
import irreechaaImage from "../../Images/oromo-irreechaa-thanks-giving-festival.webp"

export type HomeSlideImage = {
  key: string
  src: string
  altKey: string
}

export const heroSlideshowImages: HomeSlideImage[] = [
  {
    key: "library",
    src: libraryImage.src,
    altKey: "gallery.image1.alt",
  },
  {
    key: "collection",
    src: collectionImage.src,
    altKey: "gallery.image2.alt",
  },
  {
    key: "community",
    src: communityImage.src,
    altKey: "gallery.image3.alt",
  },
  {
    key: "irreechaa",
    src: irreechaaImage.src,
    altKey: "gallery.image4.alt",
  },
]

export type HomeGalleryImage = {
  key: string
  src: string
  altKey: string
  captionKey: string
}

export const homeGalleryImages: HomeGalleryImage[] = [
  {
    key: "library",
    src: libraryImage.src,
    altKey: "gallery.image1.alt",
    captionKey: "gallery.image1.caption",
  },
  {
    key: "collection",
    src: collectionImage.src,
    altKey: "gallery.image2.alt",
    captionKey: "gallery.image2.caption",
  },
  {
    key: "community",
    src: communityImage.src,
    altKey: "gallery.image3.alt",
    captionKey: "gallery.image3.caption",
  },
  {
    key: "irreechaa",
    src: irreechaaImage.src,
    altKey: "gallery.image4.alt",
    captionKey: "gallery.image4.caption",
  },
]
