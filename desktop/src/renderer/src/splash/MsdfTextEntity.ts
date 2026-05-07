import * as THREE from 'three/webgpu'
import { MSDFTextGeometry } from 'three-msdf-text-utils'
import { MSDFTextNodeMaterial } from 'three-msdf-text-utils/webgpu'
import { attribute, clamp, float, mix, mrt, smoothstep, step, texture, uniform } from 'three/tsl'

import { SPLASH_TOKENS } from './splashTokens'

/**
 * MSDF text entity — owns one mesh that renders the wordmark with a TSL
 * node material whose dissolve uniform progresses 0 → 1 to drive the
 * gommage effect.
 *
 * IMPORTANT: imports `MSDFTextNodeMaterial` from `three-msdf-text-utils/webgpu`
 * subpath. The default `three-msdf-text-utils` entry point exports the
 * old WebGL `MSDFTextMaterial` only. Production builds will fail to find
 * `MSDFTextNodeMaterial` if you import from the wrong path.
 */
export class MsdfTextEntity {
  private worldBounds: THREE.Box3 | null = null

  async initialize(
    text: string,
    position: THREE.Vector3,
    uProgress: ReturnType<typeof uniform>,
    perlinTexture: THREE.Texture,
    fontAtlasTexture: THREE.Texture
  ): Promise<THREE.Mesh> {
    const fontData = await fetch('/fonts/Cinzel/Cinzel.json').then((r) => r.json())

    const textGeometry = new MSDFTextGeometry({
      text,
      font: fontData,
      width: 1000,
      align: 'center'
    })

    const textMaterial = this.createMaterial(fontAtlasTexture, perlinTexture, uProgress)
    textMaterial.alphaTest = 0.1
    const mesh = new THREE.Mesh(textGeometry, textMaterial)

    const lineHeightPx = fontData.common.lineHeight as number
    const textScale = SPLASH_TOKENS.text.lineHeightWorld / lineHeightPx
    mesh.scale.set(textScale, textScale, textScale)
    const meshOffsetX = -(textGeometry.layout.width / 2) * textScale
    mesh.position.set(position.x + meshOffsetX, position.y, position.z)
    mesh.rotation.x = Math.PI

    // MSDFTextGeometry.d.ts doesn't surface BufferGeometry's
    // computeBoundingBox even though the runtime instance has it.
    ;(textGeometry as unknown as THREE.BufferGeometry).computeBoundingBox()
    mesh.updateWorldMatrix(true, false)
    this.worldBounds = new THREE.Box3().setFromObject(mesh)
    return mesh
  }

  getRandomPositionInMesh(): THREE.Vector3 {
    if (this.worldBounds === null) {
      throw new Error('MsdfTextEntity.initialize must be called first')
    }
    const { min, max } = this.worldBounds
    return new THREE.Vector3(
      Math.random() * (max.x - min.x) + min.x,
      Math.random() * (max.y - min.y) + min.y,
      Math.random() * 0.5
    )
  }

  private createMaterial(
    fontAtlasTexture: THREE.Texture,
    perlinTexture: THREE.Texture,
    uProgress: ReturnType<typeof uniform>
  ): MSDFTextNodeMaterial {
    const material = new MSDFTextNodeMaterial({
      map: fontAtlasTexture,
      transparent: true
    })

    const glyphUv = attribute('glyphUv', 'vec2')
    const center = attribute('center', 'vec2')

    const uNoiseRemapMin = uniform(0.48)
    const uNoiseRemapMax = uniform(0.9)
    const uCenterScale = uniform(0.05)
    const uGlyphScale = uniform(0.75)
    const uDissolvedColor = uniform(new THREE.Color(SPLASH_TOKENS.text.dissolvedColor))
    const uDesatComplete = uniform(0.45)
    const uBaseColor = uniform(new THREE.Color(SPLASH_TOKENS.text.baseColor))

    const customUv = center.mul(uCenterScale).add(glyphUv.mul(uGlyphScale))
    const perlinTextureNode = texture(perlinTexture, customUv).x
    const perlinRemap = clamp(
      perlinTextureNode.sub(uNoiseRemapMin).div(uNoiseRemapMax.sub(uNoiseRemapMin)),
      0,
      1
    )
    const dissolve = step(uProgress, perlinRemap)
    const desaturationProgress = smoothstep(float(0.0), uDesatComplete, uProgress)

    const colorMix = mix(uBaseColor, uDissolvedColor, desaturationProgress)
    material.colorNode = colorMix
    const msdfOpacity = material.opacityNode
    material.opacityNode = msdfOpacity.mul(dissolve)
    // mrtNode lives on NodeMaterial at runtime but isn't surfaced on the
    // MSDFTextNodeMaterial public type — cast through unknown to attach it.
    ;(material as unknown as { mrtNode: ReturnType<typeof mrt> }).mrtNode = mrt({
      bloomIntensity: float(0.4).mul(dissolve)
    })
    return material
  }
}
