/**
 * Splash effect constants. Centralised so timing tweaks are one-line edits.
 *
 * Durations chosen per UX research:
 *   - Doherty threshold ~400ms perception boundary
 *   - Common splash UX guideline ≤1s for everyday apps
 *   - Petal-dissolve effect needs ~1.6s of breathing room to read
 *
 * Particle pool sizes follow the Codrops reference; intervals are
 * compressed because we shrunk the duration from 6s → 1.6s and need
 * to keep visual density.
 */
export const SPLASH_TOKENS = Object.freeze({
  /** Gommage uProgress 0 → 1 timeline duration, seconds. */
  gommageDuration: 1.6,

  /** Cadence for spawning dust + petal particles, seconds.
   *  Faster than the reference's 0.125 / 0.05 to compensate for the
   *  shorter total duration. */
  dustInterval: 0.1,
  petalInterval: 0.04,

  /** Cap on simultaneous instances. Reference uses 100 / 400. */
  dustMax: 100,
  petalMax: 400,

  /** Particle lifetimes, seconds. */
  dustLife: 4,
  petalLife: 4,

  /** How long after splash completes before we unmount the canvas.
   *  Lets the trailing particles fade before yanking the GPU work. */
  unmountDelay: 0.45,

  /** Border-activity fade-out duration (CSS transition matches this). */
  borderCalmDuration: 1.4,

  /** RAF ticks to run before triggering the gommage timeline. Hides
   *  the first-frame WebGPU shader-compile stutter. */
  warmupRafTicks: 3,

  text: Object.freeze({
    /** Wordmark shown on the splash. \n is honoured by MSDFTextGeometry. */
    content: 'CHAPTER\nEXTRACTOR',
    /** Target line height in world units (camera at z=5, FOV 45°). */
    lineHeightWorld: 0.85,
    /** Pre-dissolve glyph colour — Obsidian amber accent. */
    baseColor: '#c9a96e',
    /** Colour the glyph desaturates toward as it dissolves — accent-dim. */
    dissolvedColor: '#2a2520'
  }),

  scene: Object.freeze({
    /** Renderer clear-colour. Matches --color-obs-bg-deep so the canvas
     *  blends seamlessly with the framed inner area. */
    clearColorHex: 0x090909,
    /** Bloom intensity passed to the postprocessing bloom node. */
    bloomIntensity: 0.8,
    /** Camera FOV, degrees. */
    fov: 45,
    /** Camera Z position, world units. */
    cameraZ: 5
  })
} as const)

export type SplashTokens = typeof SPLASH_TOKENS
