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
  it('descrambles a focally-garbled asset back to clean', () => {
    const n = 1024
    const phi = buildPhaseMask(PHASE_SEED, n)

    // Garble a clean stand-in at the focal dial position the same way the offline
    // tool would: scramble by +alphaForReveal(revlFocal).
    const revlFocal = 650
    const alphaFocal = alphaForReveal(revlFocal, AXIS_MAX, ALPHA_MAX)
    const clean = new Float32Array(n)
    for (let i = 0; i < n; i++) clean[i] = 0.4 * Math.sin(i * 0.05) + 0.2 * Math.sin(i * 0.011)
    const garbled = phaseTransform(clean, phi, alphaFocal)

    // Feed the garbled buffer to the engine and render at the focal dial value.
    const e = new RevealEngine(mockContext())
    e.buffer = { getChannelData: () => garbled }
    e._prepare()
    e.setReveal(revlFocal) // node is null, so no post; just sets alpha
    const out = e._render()

    let resFocal = 0
    for (let i = 0; i < n; i++) resFocal += (out[i] - clean[i]) ** 2
    resFocal /= n
    expect(resFocal).toBeLessThan(1e-6) // voice reconstructed

    // Away from the focal position the output is not the clean voice.
    e.setReveal(200)
    const off = e._render()
    let resOff = 0
    for (let i = 0; i < n; i++) resOff += (off[i] - clean[i]) ** 2
    resOff /= n
    expect(resOff).toBeGreaterThan(resFocal * 1000)
  })
})
