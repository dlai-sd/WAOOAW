import img1 from '../WAOOAW_1.webp'
import img2 from '../WAOOAW_2.webp'
import img3 from '../WAOOAW_3.webp'

export const SLIDE_COUNT = 3

const SLIDES = [
  { id: 1, src: img1, alt: 'WAOOAW — AI agent marketplace' },
  { id: 2, src: img2, alt: 'WAOOAW — AI workforce platform' },
  { id: 3, src: img3, alt: 'WAOOAW — Try before you hire' },
]

interface HeroCarouselProps {
  current: number
  onPrev: () => void
  onNext: () => void
}

export default function HeroCarousel({ current, onPrev, onNext }: HeroCarouselProps) {
  return (
    <div className="hero-carousel" aria-label="Hero image carousel">
      <div className="hero-carousel-stage">
        {SLIDES.map((slide, i) => (
          <div
            key={slide.id}
            className={`hero-carousel-track${i === current ? ' hero-carousel-track--active' : ''}`}
            aria-hidden={i !== current}
          >
            <img
              src={slide.src}
              alt={slide.alt}
              className="hero-carousel-img"
            />
          </div>
        ))}

        {/* Prev arrow */}
        <button
          className="hero-carousel-arrow hero-carousel-arrow--prev"
          onClick={onPrev}
          aria-label="Previous slide"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>

        {/* Next arrow */}
        <button
          className="hero-carousel-arrow hero-carousel-arrow--next"
          onClick={onNext}
          aria-label="Next slide"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>

        {/* Centered text overlay */}
        <div className="hero-carousel-overlay">
          <p className="hero-carousel-overlay-title">WAOOAW</p>
          <p className="hero-carousel-overlay-subtitle">Ways Of Working</p>
        </div>
      </div>
    </div>
  )
}
