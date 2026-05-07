import { useState } from 'react'

/**
 * One Mac-style window control. Three of these (close, minimize, maximize)
 * stack horizontally inside <TrafficLights/>.
 *
 * Hover reveals an SVG glyph (× / − / +) inside the dot — Apple's
 * convention. Click bubbles up via onActivate. The dot itself is 12 px
 * with a 1 px inner border for definition against acrylic backdrops.
 */
export type TrafficKind = 'close' | 'minimize' | 'maximize'

interface Props {
  kind: TrafficKind
  color: string
  onActivate: () => void
  hovered: boolean
}

export function TrafficLight({ kind, color, onActivate, hovered }: Props): React.JSX.Element {
  const [pressed, setPressed] = useState(false)

  return (
    <button
      type="button"
      aria-label={kind}
      onClick={onActivate}
      onMouseDown={() => setPressed(true)}
      onMouseUp={() => setPressed(false)}
      onMouseLeave={() => setPressed(false)}
      className="no-drag relative size-3 rounded-full transition-colors duration-100"
      style={{
        background: color,
        boxShadow: 'inset 0 0 0 0.5px rgba(0,0,0,0.18)',
        opacity: pressed ? 0.7 : 1
      }}
    >
      <Glyph kind={kind} visible={hovered} />
    </button>
  )
}

function Glyph({ kind, visible }: { kind: TrafficKind; visible: boolean }): React.JSX.Element {
  return (
    <svg
      viewBox="0 0 12 12"
      className="absolute inset-0 size-full pointer-events-none"
      style={{ opacity: visible ? 0.65 : 0, transition: 'opacity 100ms linear' }}
      aria-hidden
    >
      {kind === 'close' && (
        <>
          <line
            x1="3.5"
            y1="3.5"
            x2="8.5"
            y2="8.5"
            stroke="black"
            strokeWidth="1.2"
            strokeLinecap="round"
          />
          <line
            x1="8.5"
            y1="3.5"
            x2="3.5"
            y2="8.5"
            stroke="black"
            strokeWidth="1.2"
            strokeLinecap="round"
          />
        </>
      )}
      {kind === 'minimize' && (
        <line
          x1="2.5"
          y1="6"
          x2="9.5"
          y2="6"
          stroke="black"
          strokeWidth="1.4"
          strokeLinecap="round"
        />
      )}
      {kind === 'maximize' && (
        <>
          <line
            x1="6"
            y1="2.5"
            x2="6"
            y2="9.5"
            stroke="black"
            strokeWidth="1.4"
            strokeLinecap="round"
          />
          <line
            x1="2.5"
            y1="6"
            x2="9.5"
            y2="6"
            stroke="black"
            strokeWidth="1.4"
            strokeLinecap="round"
          />
        </>
      )}
    </svg>
  )
}
