import { Tokens } from '../theme/tokens'
import { TrafficLights } from './TrafficLights'

/**
 * Frameless titlebar. The whole strip is a drag region except the
 * traffic-lights cluster on the left. Height pinned to the design-token
 * value so the renderer agrees with the main process about how much
 * vertical space the chrome consumes.
 */
export function TitleBar(): React.JSX.Element {
  return (
    <header
      className="drag-region flex items-center w-full select-none"
      style={{ height: Tokens.size.titlebarHeight }}
    >
      <TrafficLights />
      {/* Future: centred app name / project switcher / search bar */}
      <div className="flex-1" />
    </header>
  )
}
