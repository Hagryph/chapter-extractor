/**
 * Obsidian theme tokens, mirrored from refiner.jsx in the original
 * Refiner UI. These are the source of truth for every colour, radius,
 * spacing and typography decision in the renderer.
 *
 * Single frozen object — no scattered constants, no magic strings in
 * components. Components reference `Tokens.color.bgRoot`, etc. The
 * matching CSS custom-properties live in `styles/globals.css`.
 */

export const Tokens = Object.freeze({
  color: Object.freeze({
    bgRoot: '#0e0e0f',
    bgSurface: '#111111',
    bgDeep: '#090909',
    border: '#1a1a1a',
    borderStrong: '#161616',
    borderSubtle: '#1e1e1e',
    btnBorder: '#272727',
    textPrimary: '#ddd9d0',
    textSecondary: '#888888',
    textMuted: '#555555',
    textLabel: '#3a3a3a',
    textDim: '#2a2a2a',
    accent: '#c9a96e',
    accentDim: '#2a2520',
    accentHover: 'rgba(201, 169, 110, 0.07)',
    danger: '#aa4444',
    dangerHover: 'rgba(170, 68, 68, 0.08)',
    success: '#7a9a7a',
    inputText: '#aaa69e',
    caret: '#c9a96e',
    overlayBg: 'rgba(0, 0, 0, 0.83)',
    // Mac-style traffic lights (red/yellow/green)
    macClose: '#ff5f57',
    macMinimize: '#febc2e',
    macMaximize: '#28c840'
  }),
  radius: Object.freeze({
    sm: 6,
    md: 10,
    lg: 14,
    xl: 18
  }),
  size: Object.freeze({
    titlebarHeight: 36,
    trafficLightDiameter: 12,
    trafficLightGap: 8
  }),
  motion: Object.freeze({
    fast: '120ms cubic-bezier(0.4, 0, 0.2, 1)',
    medium: '220ms cubic-bezier(0.4, 0, 0.2, 1)',
    slow: '420ms cubic-bezier(0.65, 0, 0.35, 1)'
  })
} as const)

export type ThemeTokens = typeof Tokens
