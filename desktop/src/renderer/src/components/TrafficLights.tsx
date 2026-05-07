import { useState } from 'react'

import { Tokens } from '../theme/tokens'
import { TrafficLight } from './TrafficLight'

/**
 * Mac-style window controls top-LEFT. Hovering ANY of them reveals
 * the glyph on ALL three (Apple's idiom — they reveal as a group, not
 * per-button). All three opt out of the drag region so clicks register.
 */
export function TrafficLights(): React.JSX.Element {
  const [hovered, setHovered] = useState(false)

  const close = (): void => {
    void window.api.window.close()
  }
  const minimize = (): void => {
    void window.api.window.minimize()
  }
  const maximize = (): void => {
    void window.api.window.maximizeToggle()
  }

  return (
    <div
      className="no-drag flex items-center"
      style={{ gap: Tokens.size.trafficLightGap, paddingLeft: 12 }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <TrafficLight
        kind="close"
        color={Tokens.color.macClose}
        onActivate={close}
        hovered={hovered}
      />
      <TrafficLight
        kind="minimize"
        color={Tokens.color.macMinimize}
        onActivate={minimize}
        hovered={hovered}
      />
      <TrafficLight
        kind="maximize"
        color={Tokens.color.macMaximize}
        onActivate={maximize}
        hovered={hovered}
      />
    </div>
  )
}
