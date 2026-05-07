import { type ReactNode } from 'react'

interface Props {
  /** 1.0 = full electric activity (during splash). 0 = calm static border (after). */
  activity: number
  children: ReactNode
}

/**
 * Animated frame around the app content. SVG turbulence-displacement
 * filter (BalintFerenczy's CodePen pattern, recoloured amber gold) at
 * full activity, fading to a quiet static amber outline as the
 * `activity` prop transitions from 1 to 0.
 *
 * Performance:
 *   - Only `opacity` is animated (CSS transition) — compositor-thread,
 *     no layout/paint per frame.
 *   - Glow + overlay layers get `will-change: opacity` so Chromium
 *     promotes them to GPU layers ahead of the transition.
 *   - The SVG filter itself is GPU-rasterised since Chromium 67 (2018).
 */
export function ElectricBorder({ activity, children }: Props): React.JSX.Element {
  return (
    <div
      className="window absolute inset-0 p-7"
      style={
        {
          '--activity': activity
        } as React.CSSProperties
      }
    >
      <svg
        className="svg-defs"
        aria-hidden="true"
        style={{ position: 'absolute', width: 0, height: 0, pointerEvents: 'none' }}
      >
        <defs>
          <filter
            id="turbulent-displace"
            colorInterpolationFilters="sRGB"
            x="-20%"
            y="-20%"
            width="140%"
            height="140%"
          >
            <feTurbulence
              type="turbulence"
              baseFrequency="0.02"
              numOctaves={10}
              result="noise1"
              seed={1}
            />
            <feOffset in="noise1" dx="0" dy="0" result="offsetNoise1">
              <animate attributeName="dy" values="700; 0" dur="6s" repeatCount="indefinite" />
            </feOffset>
            <feTurbulence
              type="turbulence"
              baseFrequency="0.02"
              numOctaves={10}
              result="noise2"
              seed={1}
            />
            <feOffset in="noise2" dx="0" dy="0" result="offsetNoise2">
              <animate attributeName="dy" values="0; -700" dur="6s" repeatCount="indefinite" />
            </feOffset>
            <feTurbulence
              type="turbulence"
              baseFrequency="0.02"
              numOctaves={10}
              result="noise3"
              seed={2}
            />
            <feOffset in="noise3" dx="0" dy="0" result="offsetNoise3">
              <animate attributeName="dx" values="490; 0" dur="6s" repeatCount="indefinite" />
            </feOffset>
            <feTurbulence
              type="turbulence"
              baseFrequency="0.02"
              numOctaves={10}
              result="noise4"
              seed={2}
            />
            <feOffset in="noise4" dx="0" dy="0" result="offsetNoise4">
              <animate attributeName="dx" values="0; -490" dur="6s" repeatCount="indefinite" />
            </feOffset>
            <feComposite in="offsetNoise1" in2="offsetNoise2" result="part1" />
            <feComposite in="offsetNoise3" in2="offsetNoise4" result="part2" />
            <feBlend in="part1" in2="part2" mode="color-dodge" result="combinedNoise" />
            <feDisplacementMap
              in="SourceGraphic"
              in2="combinedNoise"
              scale="30"
              xChannelSelector="R"
              yChannelSelector="B"
            />
          </filter>
        </defs>
      </svg>

      <div className="card-container">
        <div className="inner-container">
          <div className="border-outer">
            <div className="main-card" />
          </div>
          <div className="glow-layer-1" />
          <div className="glow-layer-2" />
        </div>
        <div className="overlay-1" />
        <div className="overlay-2" />
        <div className="background-glow" />

        <div className="content-container">{children}</div>
      </div>
    </div>
  )
}
