import { type ReactNode } from 'react'

import styles from './ElectricBorder.module.css'

/*
 * Source: BalintFerenczy / Codrops "Animated Electric Border" zip,
 * src/index.html. Ported VERBATIM into JSX. The only mechanical
 * changes vs upstream:
 *   - HTML attribute names become React camelCase (numOctaves,
 *     baseFrequency, repeatCount, attributeName, calcMode,
 *     xChannelSelector, yChannelSelector, colorInterpolationFilters)
 *   - class names go through CSS Modules
 * All filter values, animation timings, layer order and structure
 * are unchanged.
 */

interface ElectricBorderProps {
  children?: ReactNode
}

export function ElectricBorder({ children }: ElectricBorderProps): React.JSX.Element {
  return (
    <div className={styles.cardContainer}>
      <svg className={styles.svgContainer} aria-hidden="true">
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
              <animate
                attributeName="dy"
                values="700; 0"
                dur="6s"
                repeatCount="indefinite"
                calcMode="linear"
              />
            </feOffset>

            <feTurbulence
              type="turbulence"
              baseFrequency="0.02"
              numOctaves={10}
              result="noise2"
              seed={1}
            />
            <feOffset in="noise2" dx="0" dy="0" result="offsetNoise2">
              <animate
                attributeName="dy"
                values="0; -700"
                dur="6s"
                repeatCount="indefinite"
                calcMode="linear"
              />
            </feOffset>

            <feTurbulence
              type="turbulence"
              baseFrequency="0.02"
              numOctaves={10}
              result="noise1"
              seed={2}
            />
            <feOffset in="noise1" dx="0" dy="0" result="offsetNoise3">
              <animate
                attributeName="dx"
                values="490; 0"
                dur="6s"
                repeatCount="indefinite"
                calcMode="linear"
              />
            </feOffset>

            <feTurbulence
              type="turbulence"
              baseFrequency="0.02"
              numOctaves={10}
              result="noise2"
              seed={2}
            />
            <feOffset in="noise2" dx="0" dy="0" result="offsetNoise4">
              <animate
                attributeName="dx"
                values="0; -490"
                dur="6s"
                repeatCount="indefinite"
                calcMode="linear"
              />
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

      <div className={styles.innerContainer}>
        <div className={styles.borderOuter}>
          <div className={styles.mainCard} />
        </div>
        <div className={styles.glowLayer1} />
        <div className={styles.glowLayer2} />
      </div>

      <div className={styles.overlay1} />
      <div className={styles.overlay2} />
      <div className={styles.backgroundGlow} />

      <div className={styles.contentContainer}>{children}</div>
    </div>
  )
}
