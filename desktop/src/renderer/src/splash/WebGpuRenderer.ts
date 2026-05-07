import * as THREE from 'three/webgpu'
import { float, mrt, output, pass } from 'three/tsl'
import { bloom } from 'three/examples/jsm/tsl/display/BloomNode.js'

import { SPLASH_TOKENS } from './splashTokens'

/**
 * Wraps THREE.WebGPURenderer + the bloom postprocessing pipeline used by
 * the gommage effect.
 *
 * Lifecycle:
 *   1. constructor — instantiates renderer + scene + camera (no GPU init yet)
 *   2. await init(container) — initialises WebGPU adapter, mounts canvas,
 *      builds the postprocessing pipeline (MRT bloom)
 *   3. start() — kicks off the RAF loop; safe to call after init
 *   4. resize() — call when the host element changes size
 *   5. dispose() — cancels RAF, calls renderer.dispose() per Three.js
 *      common/Renderer.js (handles backend, geometries, materials, textures,
 *      render targets, animation, pipelines, all internal subsystems).
 *      WebGPURenderer has NO forceContextLoss — that's WebGL-only.
 */
export class WebGpuRenderer {
  private readonly renderer: THREE.WebGPURenderer
  readonly scene: THREE.Scene
  readonly camera: THREE.PerspectiveCamera
  private composer: THREE.PostProcessing | null = null
  private rafId: number | null = null
  private container: HTMLElement | null = null

  constructor() {
    this.renderer = new THREE.WebGPURenderer({ antialias: true })
    this.renderer.shadowMap.enabled = false
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping
    this.renderer.setClearColor(SPLASH_TOKENS.scene.clearColorHex, 1)

    this.scene = new THREE.Scene()
    this.camera = new THREE.PerspectiveCamera(SPLASH_TOKENS.scene.fov, 1, 0.1, 25)
    this.camera.position.set(0, 0, SPLASH_TOKENS.scene.cameraZ)
  }

  async init(container: HTMLElement): Promise<void> {
    this.container = container
    await this.renderer.init()

    const dpr = Math.min(window.devicePixelRatio ?? 1, 2)
    this.renderer.setPixelRatio(dpr)
    this.resize()
    container.appendChild(this.renderer.domElement)

    this.setupPostprocessing()
  }

  start(): void {
    if (this.rafId !== null) return
    const tick = (): void => {
      this.composer?.render()
      this.rafId = requestAnimationFrame(tick)
    }
    this.rafId = requestAnimationFrame(tick)
  }

  resize(): void {
    if (this.container === null) return
    const w = this.container.clientWidth || window.innerWidth
    const h = this.container.clientHeight || window.innerHeight
    const horizontalFovTarget = THREE.MathUtils.degToRad(SPLASH_TOKENS.scene.fov)
    this.camera.aspect = w / h
    const verticalFov = 2 * Math.atan(Math.tan(horizontalFovTarget / 2) / this.camera.aspect)
    this.camera.fov = THREE.MathUtils.radToDeg(verticalFov)
    this.camera.updateProjectionMatrix()
    this.renderer.setSize(w, h)
  }

  dispose(): void {
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId)
      this.rafId = null
    }
    this.composer = null
    this.renderer.dispose()
    if (this.renderer.domElement.parentElement !== null) {
      this.renderer.domElement.parentElement.removeChild(this.renderer.domElement)
    }
    while (this.scene.children.length > 0) {
      this.scene.remove(this.scene.children[0])
    }
  }

  private setupPostprocessing(): void {
    this.composer = new THREE.PostProcessing(this.renderer)
    const scenePass = pass(this.scene, this.camera)
    scenePass.setMRT(
      mrt({
        output,
        bloomIntensity: float(0)
      })
    )
    let outNode = scenePass
    const outputPass = scenePass.getTextureNode()
    const bloomIntensityPass = scenePass.getTextureNode('bloomIntensity')
    const bloomPass = bloom(outputPass.mul(bloomIntensityPass), SPLASH_TOKENS.scene.bloomIntensity)
    outNode = outNode.add(bloomPass)
    this.composer.outputNode = outNode.renderOutput()
    this.composer.needsUpdate = true
  }
}
