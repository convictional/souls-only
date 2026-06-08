// tests/reveal-engine.test.js
import { describe, it, expect } from 'vitest'
import { RevealEngine } from '../src/reveal-engine.js'
import { alphaForReveal, buildPhaseMask, phaseTransform } from '../src/scramble.js'
import { AXIS_MAX, ALPHA_MAX, PHASE_SEED } from '../src/constants.js'

// The constructor only needs createGain(), returning something with connect().
function mockContext() {
  return {
    currentTime: 0,
    sampleRate: 22050,
    createGain: () => ({ connect() {}, gain: { value: 1 } }),
  }
}

describe('RevealEngine alpha state', () => {
  it('starts at alpha 0 (revl 0)', () => {
    const e = new RevealEngine(mockContext())
    expect(e.revl).toBe(0)
    expect(e.alpha).toBe(0)
  })

  it('maps the dial to the phase-rotation amount via alphaForReveal', () => {
    const e = new RevealEngine(mockContext())
    e.setReveal(500)
    expect(e.alpha).toBe(alphaForReveal(500, AXIS_MAX, ALPHA_MAX))
    e.setReveal(AXIS_MAX)
    expect(e.alpha).toBe(ALPHA_MAX)
  })

  it('clamps out-of-range reveal values', () => {
    const e = new RevealEngine(mockContext())
    expect(e.setReveal(5000)).toBe(1000)
    expect(e.alpha).toBe(ALPHA_MAX)
    expect(e.setReveal(-10)).toBe(0)
    expect(e.alpha).toBe(0)
  })

  it('alpha is monotonic non-decreasing across the dial', () => {
    const e = new RevealEngine(mockContext())
    let prev = -1
    for (let revl = 0; revl <= AXIS_MAX; revl += 50) {
      e.setReveal(revl)
      expect(e.alpha).toBeGreaterThanOrEqual(prev)
      prev = e.alpha
    }
  })
})

describe('RevealEngine render reconstructs the voice at the focal dial position', () => {
  it('descrambles a focally-garbled single block back to clean', () => {
    const n = 1024
    const phi = buildPhaseMask(PHASE_SEED, n)

    const revlFocal = 650
    const alphaFocal = alphaForReveal(revlFocal, AXIS_MAX, ALPHA_MAX)
    const clean = new Float32Array(n)
    for (let i = 0; i < n; i++) clean[i] = 0.4 * Math.sin(i * 0.05) + 0.2 * Math.sin(i * 0.011)
    const garbled = phaseTransform(clean, phi, alphaFocal)

    const e = new RevealEngine(mockContext(), { blockLen: n })
    e.buffer = { getChannelData: () => garbled }
    e._prepare()
    e.setReveal(revlFocal) // node is null, so no post; just sets alpha
    const out = e._render()

    let resFocal = 0
    for (let i = 0; i < n; i++) resFocal += (out[i] - clean[i]) ** 2
    resFocal /= n
    expect(resFocal).toBeLessThan(1e-6) // voice reconstructed

    e.setReveal(200)
    const off = e._render()
    let resOff = 0
    for (let i = 0; i < n; i++) resOff += (off[i] - clean[i]) ** 2
    resOff /= n
    expect(resOff).toBeGreaterThan(resFocal * 1000)
  })

  it('resolves each station only at its own focal, independently', () => {
    const n = 1024
    const phi = buildPhaseMask(PHASE_SEED, n)
    const focalA = 300
    const focalB = 800
    const cleanA = new Float32Array(n)
    const cleanB = new Float32Array(n)
    for (let i = 0; i < n; i++) {
      cleanA[i] = 0.4 * Math.sin(i * 0.05)
      cleanB[i] = 0.3 * Math.sin(i * 0.017) + 0.2 * Math.sin(i * 0.09)
    }
    const blockA = phaseTransform(cleanA, phi, alphaForReveal(focalA, AXIS_MAX, ALPHA_MAX))
    const blockB = phaseTransform(cleanB, phi, alphaForReveal(focalB, AXIS_MAX, ALPHA_MAX))
    const asset = new Float32Array(2 * n)
    asset.set(blockA, 0)
    asset.set(blockB, n)

    const e = new RevealEngine(mockContext(), { blockLen: n })
    e.buffer = { getChannelData: () => asset }
    e._prepare()

    const mse = (out, clean, off) => {
      let s = 0
      for (let i = 0; i < n; i++) s += (out[off + i] - clean[i]) ** 2
      return s / n
    }

    e.setReveal(focalA)
    let out = e._render()
    expect(mse(out, cleanA, 0)).toBeLessThan(1e-6)
    expect(mse(out, cleanB, n)).toBeGreaterThan(1e-3)

    e.setReveal(focalB)
    out = e._render()
    expect(mse(out, cleanB, n)).toBeLessThan(1e-6)
    expect(mse(out, cleanA, 0)).toBeGreaterThan(1e-3)
  })

  it('_renderTuned plays whichever station resolves at the current dial', () => {
    const n = 1024
    const phi = buildPhaseMask(PHASE_SEED, n)
    const focalA = 300
    const focalB = 800
    // Sparse, peaky signals stand in for speech: a resolved block is super-Gaussian
    // (high kurtosis), while a non-resolved block is phase-noise near kurtosis 3, so
    // _renderTuned picks the resolved one.
    const cleanA = new Float32Array(n)
    const cleanB = new Float32Array(n)
    for (let k = 0; k < 24; k++) {
      cleanA[(k * 37 + 5) % n] = k % 2 ? 0.8 : -0.8
      cleanB[(k * 53 + 11) % n] = k % 2 ? 0.7 : -0.7
    }
    const blockA = phaseTransform(cleanA, phi, alphaForReveal(focalA, AXIS_MAX, ALPHA_MAX))
    const blockB = phaseTransform(cleanB, phi, alphaForReveal(focalB, AXIS_MAX, ALPHA_MAX))
    const asset = new Float32Array(2 * n)
    asset.set(blockA, 0)
    asset.set(blockB, n)

    const e = new RevealEngine(mockContext(), { blockLen: n })
    e.buffer = { getChannelData: () => asset }
    e._prepare()

    const mse = (out, clean) => {
      let s = 0
      for (let i = 0; i < n; i++) s += (out[i] - clean[i]) ** 2
      return s / n
    }

    e.setReveal(focalA)
    const tunedA = e._renderTuned()
    expect(tunedA.length).toBe(n)
    expect(mse(tunedA, cleanA)).toBeLessThan(1e-6)

    e.setReveal(focalB)
    const tunedB = e._renderTuned()
    expect(mse(tunedB, cleanB)).toBeLessThan(1e-6)
  })
})
