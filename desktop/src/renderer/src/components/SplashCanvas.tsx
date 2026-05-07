import { useEffect, useRef } from 'react'

import { SplashOrchestrator } from '../splash/SplashOrchestrator'
import { WebGpuRenderer } from '../splash/WebGpuRenderer'
import { SPLASH_TOKENS } from '../splash/splashTokens'

interface Props {
  /** Fired once after the gommage timeline finishes (after the unmount-delay). */
  onComplete: () => void
}

/**
 * React host for the Three.js + WebGPU splash. Handles mount/unmount
 * lifecycle around the imperative renderer per the Three.js cleanup
 * contract:
 *
 *   1. WebGpuRenderer.init(container) — async; creates the canvas
 *   2. SplashOrchestrator.initialize(scene) — loads textures + GLB
 *   3. WebGpuRenderer.start() — RAF loop
 *   4. wait `warmupRafTicks` frames so shaders are compiled
 *   5. SplashOrchestrator.start() — kicks the GSAP timeline
 *   6. onComplete after timeline + unmountDelay
 *
 * Cleanup chain (matches three.js Renderer.dispose semantics + the
 * Three.js cleanup guidance from https://threejs.org/manual):
 *   - SplashOrchestrator.dispose()  kills GSAP tweens
 *   - WebGpuRenderer.dispose()      cancels RAF, calls renderer.dispose
 *                                   which handles backend, geometries,
 *                                   materials, textures, render targets,
 *                                   pipelines internally; removes canvas
 *                                   from DOM; clears scene.children
 */
export function SplashCanvas({ onComplete }: Props): React.JSX.Element {
  const containerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const container = containerRef.current
    if (container === null) return

    let cancelled = false
    let renderer: WebGpuRenderer | null = null
    let orchestrator: SplashOrchestrator | null = null
    let resizeHandler: (() => void) | null = null

    const run = async (): Promise<void> => {
      renderer = new WebGpuRenderer()
      await renderer.init(container)
      if (cancelled) return

      orchestrator = new SplashOrchestrator()
      await orchestrator.initialize(renderer.scene)
      if (cancelled) return

      renderer.start()

      // Warm up shaders — render a few frames before the user-visible
      // animation begins. WebGPU compiles pipelines on first use, which
      // can stutter; running RAF first hides the cost.
      await waitForRaf(SPLASH_TOKENS.warmupRafTicks)
      if (cancelled) return

      resizeHandler = (): void => renderer?.resize()
      window.addEventListener('resize', resizeHandler)

      await orchestrator.start()
      if (cancelled) return

      // Let the trailing particles fade before unmounting.
      window.setTimeout(() => {
        if (!cancelled) onComplete()
      }, SPLASH_TOKENS.unmountDelay * 1000)
    }

    void run()

    return (): void => {
      cancelled = true
      if (resizeHandler !== null) window.removeEventListener('resize', resizeHandler)
      orchestrator?.dispose()
      renderer?.dispose()
    }
    // The onComplete callback is captured once on mount; downstream changes
    // wouldn't matter because the splash plays exactly once per mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div
      ref={containerRef}
      className="absolute inset-0"
      style={{ willChange: 'opacity', contain: 'strict' }}
      aria-hidden
    />
  )
}

/** Resolves after `n` requestAnimationFrame ticks. */
function waitForRaf(n: number): Promise<void> {
  return new Promise<void>((resolve) => {
    let i = 0
    const tick = (): void => {
      i += 1
      if (i >= n) {
        resolve()
      } else {
        requestAnimationFrame(tick)
      }
    }
    requestAnimationFrame(tick)
  })
}
