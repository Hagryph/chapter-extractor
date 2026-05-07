import { useCallback, useState } from 'react'

import { ElectricBorder } from './components/ElectricBorder'
import { SplashCanvas } from './components/SplashCanvas'
import { TitleBar } from './components/TitleBar'

type Phase = 'splashing' | 'calming' | 'ready'

/**
 * App state machine driving the splash → border → app handoff:
 *
 *   'splashing'   SplashCanvas mounted, ElectricBorder activity = 1,
 *                 backdrop = acrylic (set in MainWindow constructor)
 *   'calming'     onSplashComplete fired: SplashCanvas unmounted, border
 *                 activity transitions 1 → 0 over CSS, IPC tells main to
 *                 swap acrylic → mica (one-way, ~1.4s)
 *   'ready'       static calm border, app interior empty for now
 *
 * The acrylic→mica swap goes through `window.api.window.setBackdrop` which
 * was registered in IpcRouter (PR 1).
 */
export default function App(): React.JSX.Element {
  const [phase, setPhase] = useState<Phase>('splashing')

  const onSplashComplete = useCallback((): void => {
    setPhase('calming')
    void window.api.window.setBackdrop('mica')
    // Border CSS transition fires here via the activity prop change.
    // After it finishes (1.4s) we move to 'ready' to drop the splashing
    // CSS class entirely.
    window.setTimeout(() => setPhase('ready'), 1400)
  }, [])

  const activity = phase === 'splashing' ? 1 : 0

  return (
    <div className="h-screen w-screen flex flex-col">
      <TitleBar />
      <main className="relative flex-1">
        <ElectricBorder activity={activity}>
          {phase === 'splashing' && <SplashCanvas onComplete={onSplashComplete} />}
        </ElectricBorder>
      </main>
    </div>
  )
}
