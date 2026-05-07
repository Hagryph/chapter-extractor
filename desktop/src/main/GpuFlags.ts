import { app } from 'electron'

/**
 * Centralised GPU command-line switches.
 *
 * Sources:
 *   - Electron docs: https://www.electronjs.org/docs/latest/api/command-line-switches
 *     (force_high_performance_gpu is officially documented)
 *   - Chromium GPU acceleration: https://chromium.googlesource.com/chromium/src/+/HEAD/docs/gpu_acceleration.md
 *   - electron-userland threads: ignore-gpu-blocklist + gpu-rasterization unblock
 *     hardware paths Chromium otherwise greys out.
 *
 * NOT included on purpose:
 *   - --disable-gpu-vsync (causes tearing)
 *   - --disable-frame-rate-limit (wastes battery; we want capped 60fps)
 *
 * Must be applied BEFORE app.whenReady() — Electron locks command line
 * once the GPU process spins up.
 */
export class GpuFlags {
  private static readonly SWITCHES: readonly string[] = [
    'force_high_performance_gpu', // discrete GPU on hybrid laptops
    'ignore-gpu-blocklist', // bypass Chromium's conservative blocklist
    'enable-gpu-rasterization', // GPU-accelerate canvas/CSS rasterisation
    'enable-zero-copy' // skip CPU→GPU memory copies
  ] as const

  private static readonly FEATURES: readonly string[] = [
    'CanvasOopRasterization' // out-of-process rasterisation, frees main thread
  ] as const

  static applyAll(): void {
    for (const sw of this.SWITCHES) {
      app.commandLine.appendSwitch(sw)
    }
    app.commandLine.appendSwitch('enable-features', this.FEATURES.join(','))
  }
}
