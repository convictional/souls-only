// tests/babble.test.js
import { describe, it, expect } from 'vitest'
import { frameShuffle } from '../tools/babble.mjs'

function kurtosis(a) {
  let mean = 0
  for (const v of a) mean += v
  mean /= a.length
  let m2 = 0
  let m4 = 0
  for (const v of a) {
    const d = v - mean
    m2 += d * d
    m4 += d * d * d * d
  }
  m2 /= a.length
  m4 /= a.length
  return m4 / (m2 * m2)
}

// Coefficient of variation of short-time energy — the attacker's envelope metric.
function envCV(a, W) {
  const blocks = Math.floor(a.length / W)
  const e = new Float64Array(blocks)
  for (let b = 0; b < blocks; b++) {
    let s = 0
    for (let i = 0; i < W; i++) {
      const v = a[b * W + i]
      s += v * v
    }
    e[b] = Math.sqrt(s / W)
  }
  let m = 0
  for (const v of e) m += v
  m /= blocks
  let v2 = 0
  for (const v of e) v2 += (v - m) * (v - m)
  v2 /= blocks
  return Math.sqrt(v2) / m
}

describe('frameShuffle', () => {
  const n = 8192
  const frameLen = 256
  // A bursty, speech-like envelope: loud frames and quiet frames.
  const sig = new Float32Array(n)
  for (let i = 0; i < n; i++) {
    const loud = Math.floor(i / frameLen) % 3 === 0
    sig[i] = (loud ? 0.6 : 0.05) * Math.sin(i * 0.03)
  }

  it('preserves length', () => {
    expect(frameShuffle(sig, 1, frameLen).length).toBe(n)
  })

  it('preserves the exact sample multiset (so kurtosis is identical)', () => {
    const out = frameShuffle(sig, 7, frameLen)
    const a = Array.from(sig).sort((x, y) => x - y)
    const b = Array.from(out).sort((x, y) => x - y)
    for (let i = 0; i < n; i++) expect(b[i]).toBe(a[i])
    expect(kurtosis(out)).toBeCloseTo(kurtosis(sig), 10)
  })

  it('preserves the energy-envelope CV when frames align with the CV window', () => {
    // Shuffling whole frames permutes the per-frame energies, leaving their
    // multiset — and therefore std/mean — unchanged.
    expect(envCV(frameShuffle(sig, 7, frameLen), frameLen)).toBeCloseTo(envCV(sig, frameLen), 10)
  })

  it('is deterministic per seed', () => {
    expect(Array.from(frameShuffle(sig, 42, frameLen))).toEqual(Array.from(frameShuffle(sig, 42, frameLen)))
  })

  it('actually reorders frames (decoy differs from the source)', () => {
    const out = frameShuffle(sig, 3, frameLen)
    let differ = false
    for (let i = 0; i < n; i++) if (out[i] !== sig[i]) { differ = true; break }
    expect(differ).toBe(true)
  })

  it('different seeds give different orderings', () => {
    expect(Array.from(frameShuffle(sig, 1, frameLen))).not.toEqual(Array.from(frameShuffle(sig, 2, frameLen)))
  })
})
