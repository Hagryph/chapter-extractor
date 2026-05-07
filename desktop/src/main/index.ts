import { AppLifecycle } from './AppLifecycle'
import { GpuFlags } from './GpuFlags'

/**
 * Entry point. Two responsibilities:
 *   1. Apply GPU command-line switches BEFORE app.whenReady — they have to
 *      be set on the command line before the GPU process spins up.
 *   2. Hand off to AppLifecycle which owns everything else.
 */
GpuFlags.applyAll()
new AppLifecycle().start()
