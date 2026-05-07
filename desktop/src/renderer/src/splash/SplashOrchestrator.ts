import * as THREE from 'three/webgpu'
import { uniform } from 'three/tsl'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import gsap from 'gsap'

import { DustParticles } from './DustParticles'
import { MsdfTextEntity } from './MsdfTextEntity'
import { PetalParticles } from './PetalParticles'
import { SPLASH_TOKENS } from './splashTokens'

/**
 * Owns the splash effect lifecycle:
 *
 *   1. initialize(scene)  loads textures + GLB, instantiates the three
 *                         entities (text, dust, petals), adds them to
 *                         the supplied scene
 *   2. start()            kicks off three GSAP tweens — uProgress 0→1,
 *                         dust spawner, petal spawner — and resolves
 *                         the returned promise when all three complete
 *   3. dispose()          kills any in-flight tweens (idempotent)
 *
 * The orchestrator owns no rendering — it only mutates uProgress and
 * spawns particles. The actual frames are rendered by WebGpuRenderer.
 */
export class SplashOrchestrator {
  private readonly uProgress = uniform(0.0)

  private text: MsdfTextEntity | null = null
  private dust: DustParticles | null = null
  private petals: PetalParticles | null = null

  private gommageTween: gsap.core.Tween | null = null
  private dustSpawnTween: gsap.core.Tween | null = null
  private petalSpawnTween: gsap.core.Tween | null = null

  async initialize(scene: THREE.Scene): Promise<void> {
    const { perlinTexture, dustParticleTexture, fontAtlasTexture } = await this.loadTextures()
    const petalGeometry = await this.loadPetalGeometry()

    this.text = new MsdfTextEntity()
    const textMesh = await this.text.initialize(
      SPLASH_TOKENS.text.content,
      new THREE.Vector3(0, 0, 0),
      this.uProgress,
      perlinTexture,
      fontAtlasTexture
    )
    scene.add(textMesh)

    this.dust = new DustParticles()
    const dustMesh = await this.dust.initialize(perlinTexture, dustParticleTexture)
    scene.add(dustMesh)

    this.petals = new PetalParticles()
    const petalMesh = await this.petals.initialize(perlinTexture, petalGeometry)
    scene.add(petalMesh)
  }

  start(): Promise<void> {
    return new Promise<void>((resolve) => {
      if (this.text === null || this.dust === null || this.petals === null) {
        resolve()
        return
      }
      this.uProgress.value = 0

      this.dustSpawnTween = gsap.to(
        {},
        {
          duration: SPLASH_TOKENS.dustInterval,
          repeat: -1,
          onRepeat: () => {
            const p = this.text!.getRandomPositionInMesh()
            this.dust!.spawn(p)
          }
        }
      )

      this.petalSpawnTween = gsap.to(
        {},
        {
          duration: SPLASH_TOKENS.petalInterval,
          repeat: -1,
          onRepeat: () => {
            const p = this.text!.getRandomPositionInMesh()
            this.petals!.spawn(p)
          }
        }
      )

      this.gommageTween = gsap.to(this.uProgress, {
        value: 1,
        duration: SPLASH_TOKENS.gommageDuration,
        ease: 'linear',
        onComplete: () => {
          this.dustSpawnTween?.kill()
          this.petalSpawnTween?.kill()
          this.dustSpawnTween = null
          this.petalSpawnTween = null
          this.gommageTween = null
          resolve()
        }
      })
    })
  }

  dispose(): void {
    this.gommageTween?.kill()
    this.dustSpawnTween?.kill()
    this.petalSpawnTween?.kill()
    this.gommageTween = null
    this.dustSpawnTween = null
    this.petalSpawnTween = null
  }

  // ── private helpers ────────────────────────────────────────────────

  private async loadTextures(): Promise<{
    perlinTexture: THREE.Texture
    dustParticleTexture: THREE.Texture
    fontAtlasTexture: THREE.Texture
  }> {
    const loader = new THREE.TextureLoader()

    const dustParticleTexture = await loader.loadAsync('/textures/dustParticle.png')
    dustParticleTexture.colorSpace = THREE.NoColorSpace
    dustParticleTexture.minFilter = THREE.LinearFilter
    dustParticleTexture.magFilter = THREE.LinearFilter
    dustParticleTexture.generateMipmaps = false

    const perlinTexture = await loader.loadAsync('/textures/perlin.webp')
    perlinTexture.colorSpace = THREE.NoColorSpace
    perlinTexture.minFilter = THREE.LinearFilter
    perlinTexture.magFilter = THREE.LinearFilter
    perlinTexture.wrapS = THREE.RepeatWrapping
    perlinTexture.wrapT = THREE.RepeatWrapping
    perlinTexture.generateMipmaps = false

    const fontAtlasTexture = await loader.loadAsync('/fonts/Cinzel/Cinzel.png')
    fontAtlasTexture.colorSpace = THREE.NoColorSpace
    fontAtlasTexture.minFilter = THREE.LinearFilter
    fontAtlasTexture.magFilter = THREE.LinearFilter
    fontAtlasTexture.wrapS = THREE.ClampToEdgeWrapping
    fontAtlasTexture.wrapT = THREE.ClampToEdgeWrapping
    fontAtlasTexture.generateMipmaps = false

    return { perlinTexture, dustParticleTexture, fontAtlasTexture }
  }

  private async loadPetalGeometry(): Promise<THREE.BufferGeometry> {
    const modelLoader = new GLTFLoader()
    const petalScene = await modelLoader.loadAsync('/models/petal.glb')
    const petalMesh = petalScene.scene.getObjectByName('PetalV2') as THREE.Mesh | undefined
    if (petalMesh === undefined) {
      throw new Error('petal.glb does not contain a mesh named "PetalV2"')
    }
    return petalMesh.geometry
  }
}
