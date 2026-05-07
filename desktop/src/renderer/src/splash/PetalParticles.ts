import * as THREE from 'three/webgpu'
import {
  abs,
  attribute,
  clamp,
  cos,
  dot,
  float,
  instanceIndex,
  mat3,
  mix,
  mrt,
  normalize,
  normalLocal,
  positionLocal,
  pow,
  sin,
  smoothstep,
  texture,
  time,
  TWO_PI,
  uniform,
  uv,
  vec2,
  vec3
} from 'three/tsl'

import { SPLASH_TOKENS } from './splashTokens'

/**
 * Instanced petal pool. ~400 instances reused via a ring buffer. Each
 * spawned petal drifts on a perlin wind field, rises, spins on three
 * axes, and bends along its long axis. Petal colour alternates between
 * a deep red and a near-white (per-instance modulo). Bloom is
 * contributed via MRT.
 *
 * Adapted from the Codrops reference (see references/ in earlier work).
 */
export class PetalParticles {
  private spawnPos: Float32Array
  private birthLifeSeedScale: Float32Array
  private currentIndex = 0
  private mesh: THREE.InstancedMesh | null = null

  constructor() {
    this.spawnPos = new Float32Array(SPLASH_TOKENS.petalMax * 3)
    this.birthLifeSeedScale = new Float32Array(SPLASH_TOKENS.petalMax * 4)
  }

  async initialize(
    perlinTexture: THREE.Texture,
    petalGeometry: THREE.BufferGeometry
  ): Promise<THREE.InstancedMesh> {
    const petalGeo = petalGeometry.clone()
    const scale = 0.1
    petalGeo.scale(scale, scale, scale)

    petalGeo.setAttribute('aSpawnPos', new THREE.InstancedBufferAttribute(this.spawnPos, 3))
    petalGeo.setAttribute(
      'aBirthLifeSeedScale',
      new THREE.InstancedBufferAttribute(this.birthLifeSeedScale, 4)
    )

    const material = this.createMaterial(perlinTexture)
    this.mesh = new THREE.InstancedMesh(petalGeo, material, SPLASH_TOKENS.petalMax)
    return this.mesh
  }

  spawn(at: THREE.Vector3): void {
    if (this.mesh === null) return
    if (this.currentIndex === SPLASH_TOKENS.petalMax) this.currentIndex = 0
    const id = this.currentIndex
    this.currentIndex += 1
    this.spawnPos[id * 3 + 0] = at.x
    this.spawnPos[id * 3 + 1] = at.y
    this.spawnPos[id * 3 + 2] = at.z
    this.birthLifeSeedScale[id * 4 + 0] = performance.now() * 0.001
    this.birthLifeSeedScale[id * 4 + 1] = SPLASH_TOKENS.petalLife
    this.birthLifeSeedScale[id * 4 + 2] = Math.random()
    this.birthLifeSeedScale[id * 4 + 3] = Math.random() * 0.5 + 0.5
    const geo = this.mesh.geometry
    geo.attributes.aSpawnPos.needsUpdate = true
    geo.attributes.aBirthLifeSeedScale.needsUpdate = true
  }

  private createMaterial(perlinTexture: THREE.Texture): THREE.MeshBasicNodeMaterial {
    const material = new THREE.MeshBasicNodeMaterial({
      transparent: true,
      side: THREE.DoubleSide
    })

    // Local helpers for axis rotation matrices in TSL.
    const rotX = (a: ReturnType<typeof time.add>): ReturnType<typeof mat3> => {
      const c = cos(a)
      const s = sin(a)
      const ns = s.mul(-1.0)
      return mat3(1.0, 0.0, 0.0, 0.0, c, ns, 0.0, s, c)
    }
    const rotY = (a: ReturnType<typeof time.add>): ReturnType<typeof mat3> => {
      const c = cos(a)
      const s = sin(a)
      const ns = s.mul(-1.0)
      return mat3(c, 0.0, s, 0.0, 1.0, 0.0, ns, 0.0, c)
    }
    const rotZ = (a: ReturnType<typeof time.add>): ReturnType<typeof mat3> => {
      const c = cos(a)
      const s = sin(a)
      const ns = s.mul(-1.0)
      return mat3(c, ns, 0.0, s, c, 0.0, 0.0, 0.0, 1.0)
    }

    const aSpawnPos = attribute('aSpawnPos', 'vec3')
    const aBLSS = attribute('aBirthLifeSeedScale', 'vec4')
    const aBirth = aBLSS.x
    const aLife = aBLSS.y
    const aSeed = aBLSS.z
    const aScale = aBLSS.w

    const uWindDirection = uniform(new THREE.Vector3(-1, 0, 0).normalize())
    const uWindStrength = uniform(0.3)
    const uRiseSpeed = uniform(0.1)
    const uNoiseScale = uniform(30.0)
    const uNoiseSpeed = uniform(0.015)
    const uWobbleAmp = uniform(0.6)

    const uBendAmount = uniform(2.5)
    const uBendSpeed = uniform(1.0)
    const uSpinSpeed = uniform(2.0)
    const uSpinAmp = uniform(0.45)
    const uRedColor = uniform(new THREE.Color('#9B0000'))
    const uWhiteColor = uniform(new THREE.Color('#EEEEEE'))
    const uLightPosition = uniform(new THREE.Vector3(0, 0, 5))

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
    const turbulenceZ = noiseSample.sub(0.5).mul(2)

    const swirl = vec3(
      clamp(turbulenceX.mul(lifeInterp), 0, 1.0),
      turbulenceY.mul(lifeInterp),
      0.0
    ).mul(uWobbleAmp)

    // Petal bend (along its long axis, weighted toward the tip).
    const y = uv().y
    const bendWeight = pow(y, float(3.0))
    const bend = bendWeight.mul(uBendAmount).mul(sin(dustAge.mul(uBendSpeed.mul(noiseSample))))
    const B = rotX(bend)

    const windImpulse = uWindDirection.mul(uWindStrength).mul(dustAge)
    const riseFactor = clamp(noiseSample, 0.3, 1.0)
    const rise = vec3(0.0, dustAge.mul(uRiseSpeed).mul(riseFactor), 0.0)
    const driftMovement = windImpulse.add(rise).add(swirl)

    // Three-axis spin from per-instance seed offsets.
    const baseX = aSeed.mul(1.13).mod(1.0).mul(TWO_PI)
    const baseY = aSeed.mul(2.17).mod(1.0).mul(TWO_PI)
    const baseZ = aSeed.mul(3.31).mod(1.0).mul(TWO_PI)
    const spin = dustAge.mul(uSpinSpeed).mul(uSpinAmp)
    const rx = baseX.add(spin.mul(0.9).mul(turbulenceX.add(1.5)))
    const ry = baseY.add(spin.mul(1.2).mul(turbulenceY.add(1.5)))
    const rz = baseZ.add(spin.mul(0.7).mul(turbulenceZ.add(1.5)))
    const R = rotY(ry).mul(rotX(rx)).mul(rotZ(rz))

    const scaleFactor = smoothstep(float(0), float(0.05), lifeInterp)
    const fadingOut = float(1.0).sub(smoothstep(float(0.8), float(1.0), lifeInterp))

    const positionLocalUpdated = R.mul(B.mul(positionLocal))
    const normalUpdate = normalize(R.mul(B.mul(normalLocal)))

    const worldPosition = aSpawnPos
      .add(driftMovement)
      .add(positionLocalUpdated.mul(aScale.mul(scaleFactor)))

    // Alternate red / white per instance modulo 3 (matches reference).
    const petalColor = mix(uRedColor, uWhiteColor, instanceIndex.mod(3).equal(0))

    const lightDirection = normalize(uLightPosition.sub(worldPosition))
    const facing = clamp(abs(dot(normalUpdate, lightDirection)), 0.4, 1)

    material.colorNode = petalColor.mul(facing)
    material.positionNode = worldPosition
    material.opacityNode = fadingOut
    material.mrtNode = mrt({
      bloomIntensity: float(0.7).mul(fadingOut)
    })
    return material
  }
}
