// tests/scramble.test.js
import { describe, it, expect } from 'vitest'
import { buildPhaseMask, alphaForReveal, phaseTransform } from '../src/scramble.js'

describe('alphaForReveal', () => {
  it('maps the dial linearly to [0, alphaMax]', () => {
    expect(alphaForReveal(0, 1000, 4)).toBe(0)
    expect(alphaForReveal(1000, 1000, 4)).toBe(4)
    expect(alphaForReveal(500, 1000, 4)).toBe(2)
  })

  it('clamps out-of-range input', () => {
    expect(alphaForReveal(-50, 1000, 4)).toBe(0)
    expect(alphaForReveal(5000, 1000, 4)).toBe(4)
  })

  it('is monotonic across the dial', () => {
    let prev = -1
    for (let revl = 0; revl <= 1000; revl += 50) {
      const a = alphaForReveal(revl, 1000, 4)
      expect(a).toBeGreaterThanOrEqual(prev)
      prev = a
    }
  })
})

describe('buildPhaseMask', () => {
  it('is deterministic per seed and conjugate-symmetric', () => {
    const n = 64
    const a = buildPhaseMask(123, n)
    const b = buildPhaseMask(123, n)
    expect(Array.from(a)).toEqual(Array.from(b))
    expect(a[0]).toBe(0)
    expect(a[n / 2]).toBe(0)
    for (let k = 1; k < n / 2; k++) {
      expect(a[n - k]).toBeCloseTo(-a[k], 12)
      expect(Math.abs(a[k])).toBeLessThanOrEqual(Math.PI)
    }
  })
})

describe('phaseTransform cancellation (the focal behavior)', () => {
  const n = 1024
  const phi = buildPhaseMask(99, n)
  const alphaF = 2.6

  // A speech-like stand-in: a few low-frequency components.
  const clean = new Float32Array(n)
  for (let i = 0; i < n; i++) {
    clean[i] = 0.4 * Math.sin(i * 0.05) + 0.2 * Math.sin(i * 0.013 + 1)
  }

  const garbled = phaseTransform(clean, phi, alphaF)

  const residualAt = (alpha) => {
    // Descramble the garbled signal by rotating the opposite way.
    const out = phaseTransform(garbled, phi, -alpha)
    let s = 0
    for (let i = 0; i < n; i++) {
      const d = out[i] - clean[i]
      s += d * d
    }
    return s / n
  }

  it('the garbled signal is real and differs from clean (genuinely transformed)', () => {
    let diff = 0
    let energyClean = 0
    let energyGarbled = 0
    for (let i = 0; i < n; i++) {
      diff += (garbled[i] - clean[i]) ** 2
      energyClean += clean[i] ** 2
      energyGarbled += garbled[i] ** 2
    }
    expect(diff / n).toBeGreaterThan(1e-3) // clearly different waveform
    // Phase-only rotation preserves spectral energy (Parseval): total energy matches.
    expect(energyGarbled).toBeCloseTo(energyClean, 3)
  })

  it('descrambling at the matching alpha recovers clean', () => {
    expect(residualAt(alphaF)).toBeLessThan(1e-6)
  })

  it('residual grows as alpha moves away from the focal amount on both sides', () => {
    const r0 = residualAt(alphaF)
    expect(residualAt(alphaF + 0.3)).toBeGreaterThan(r0)
    expect(residualAt(alphaF + 1.0)).toBeGreaterThan(residualAt(alphaF + 0.3))
    expect(residualAt(alphaF - 0.3)).toBeGreaterThan(r0)
    expect(residualAt(alphaF - 1.0)).toBeGreaterThan(residualAt(alphaF - 0.3))
  })
})
