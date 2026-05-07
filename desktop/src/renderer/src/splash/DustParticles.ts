import * as THREE from 'three/webgpu'
import {
  attribute,
  clamp,
  float,
  mrt,
  positionLocal,
  smoothstep,
  texture,
  time,
  uniform,
  uv,
  vec2,
  vec3,
  vec4
} from 'three/tsl'

import { SPLASH_TOKENS } from './splashTokens'

/**
 * Instanced dust pool. ~100 instances reused via a ring buffer. Each
 * spawned particle drifts on a perlin-driven wind field, rises, and
 * fades out over its lifetime. Bloom is contributed via MRT so the
 * post-processing bloom pass picks it up.
 */
export class DustParticles {
  private spawnPos: Float32Array
  private birthLifeSeedScale: Float32Array
  private currentIndex = 0
  private mesh: THREE.InstancedMesh | null = null

  constructor() {
    this.spawnPos = new Float32Array(SPLASH_TOKENS.dustMax * 3)
    this.birthLifeSeedScale = new Float32Array(SPLASH_TOKENS.dustMax * 4)
  }

  async initialize(
    perlinTexture: THREE.Texture,
    dustParticleTexture: THREE.Texture
  ): Promise<THREE.InstancedMesh> {
    const dustGeometry = new THREE.PlaneGeometry(0.02, 0.02)
    dustGeometry.setAttribute('aSpawnPos', new THREE.InstancedBufferAttribute(this.spawnPos, 3))
    dustGeometry.setAttribute(
      'aBirthLifeSeedScale',
      new THREE.InstancedBufferAttribute(this.birthLifeSeedScale, 4)
    )
    const material = this.createMaterial(perlinTexture, dustParticleTexture)
    this.mesh = new THREE.InstancedMesh(dustGeometry, material, SPLASH_TOKENS.dustMax)
    return this.mesh
  }

  spawn(at: THREE.Vector3): void {
    if (this.mesh === null) return
    if (this.currentIndex === SPLASH_TOKENS.dustMax) this.currentIndex = 0
    const id = this.currentIndex
    this.currentIndex += 1
    this.spawnPos[id * 3 + 0] = at.x
    this.spawnPos[id * 3 + 1] = at.y
    this.spawnPos[id * 3 + 2] = at.z
    this.birthLifeSeedScale[id * 4 + 0] = performance.now() * 0.001
    this.birthLifeSeedScale[id * 4 + 1] = SPLASH_TOKENS.dustLife
    this.birthLifeSeedScale[id * 4 + 2] = Math.random()
    this.birthLifeSeedScale[id * 4 + 3] = Math.random() * 0.5 + 0.5
    const geo = this.mesh.geometry
    geo.attributes.aSpawnPos.needsUpdate = true
    geo.attributes.aBirthLifeSeedScale.needsUpdate = true
  }

  private createMaterial(
    perlinTexture: THREE.Texture,
    dustTexture: THREE.Texture
  ): THREE.MeshBasicNodeMaterial {
    const material = new THREE.MeshBasicNodeMaterial({
      transparent: true,
      depthWrite: false,
      depthTest: false
    })

    const aSpawnPos = attribute('aSpawnPos', 'vec3')
    const aBLSS = attribute('aBirthLifeSeedScale', 'vec4')
    const aBirth = aBLSS.x
    const aLife = aBLSS.y
    const aSeed = aBLSS.z
    const aScale = aBLSS.w

    const uDustColor = uniform(new THREE.Color('#8A8A8A'))
    const uWindDirection = uniform(new THREE.Vector3(-1, 0, 0).normalize())
    const uWindStrength = uniform(0.3)
    const uRiseSpeed = uniform(0.1)
    const uNoiseScale = uniform(30.0)
    const uNoiseSpeed = uniform(0.015)
    const uWobbleAmp = uniform(0.6)

    const dustAge = time.sub(aBirth)
    const lifeInterp = clamp(dustAge.div(aLife), 0, 1)

    const randomSeed = vec2(aSeed.mul(123.4), aSeed.mul(567.8))
    const noiseUv = aSpawnPos.xz
      .mul(uNoiseScale)
      .add(randomSeed)
      .add(uWindDirection.xz.mul(dustAge.mul(uNoiseSpeed)))

    const noiseSample = texture(perlinTexture, noiseUv).x
    const noiseSampleBis = texture(perlinTexture, noiseUv.add(vec2(13.37, 7.77))).x

    const turbulenceX = noiseSample.sub(0.5).mul(2)
    const turbulenceY = noiseSampleBis.sub(0.5).mul(2)

    const swirl = vec3(
      clamp(turbulenceX.mul(lifeInterp), 0, 1.0),
      turbulenceY.mul(lifeInterp),
      0.0
    ).mul(uWobbleAmp)

    const windImpulse = uWindDirection.mul(uWindStrength).mul(dustAge)
    const riseFactor = clamp(noiseSample, 0.3, 1.0)
    const rise = vec3(0.0, dustAge.mul(uRiseSpeed).mul(riseFactor), 0.0)
    const driftMovement = windImpulse.add(rise).add(swirl)

    const scaleFactor = smoothstep(float(0), float(0.05), lifeInterp)
    const fadingOut = float(1.0).sub(smoothstep(float(0.8), float(1.0), lifeInterp))

    const dustSample = texture(dustTexture, uv())
    material.colorNode = vec4(uDustColor, dustSample.a)
    material.positionNode = aSpawnPos
      .add(driftMovement)
      .add(positionLocal.mul(aScale.mul(scaleFactor)))
    material.opacityNode = fadingOut
    material.mrtNode = mrt({
      bloomIntensity: float(0.5).mul(fadingOut)
    })
    return material
  }
}
