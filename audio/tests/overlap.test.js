// tests/overlap.test.js
// The overlap (code-division) variant: instead of concatenating N stations in
// time, sum N phase-coded clips into ONE block of the same length as a single
// clip. Descrambling at clip j's focal must recover clip j as the dominant
// signal, while the other clips stay scrambled (additive noise).
import { describe, it, expect } from 'vitest'
import { buildOverlap, tileToLength } from '../tools/overlap.mjs'
import { buildPhaseMask, alphaForReveal, phaseTransform } from '../src/scramble.js'
import { mulberry32 } from '../src/rng.js'

const N = 1024
const AXIS_MAX = 1000
const ALPHA_MAX = 10
const FOCALS = [100, 500, 900]

// A deterministic, real-valued "clip" confined to its own disjoint frequency
// band (band `idx`), so distinct clips are near-orthogonal and the dominance of
// the recovered clip is observable without intrinsic clip-to-clip correlation.
function makeClip(seed, idx) {
  const rng = mulberry32(seed)
  const base = 4 + idx * 8           // band start in FFT bins; 8 bins wide, no overlap
  const a = Array.from({ length: 6 }, () => rng() * 2 - 1)
  const p = Array.from({ length: 6 }, () => rng() * Math.PI * 2)
  const out = new Float32Array(N)
  for (let i = 0; i < N; i++) {
    let v = 0
    for (let h = 0; h < 6; h++) {
      const w = (2 * Math.PI * (base + h)) / N   // h-th bin of this clip's band
      v += a[h] * Math.sin(w * i + p[h])
    }
    out[i] = v
  }
  // level-match to unit RMS, as the real builder peak-normalizes every clip so no
  // station is louder than another
  let e = 0
  for (let i = 0; i < N; i++) e += out[i] * out[i]
  const g = 1 / (Math.sqrt(e / N) || 1)
  for (let i = 0; i < N; i++) out[i] *= g
  return out
}

// Normalized correlation (cosine similarity) of two real signals.
function corr(a, b) {
  let dot = 0, na = 0, nb = 0
  for (let i = 0; i < a.length; i++) { dot += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i] }
  return dot / (Math.sqrt(na * nb) || 1)
}

describe('tileToLength: loop a short clip to fill a longer block', () => {
  it('repeats the source to exactly the target length', () => {
    const out = tileToLength(Float32Array.from([1, 2, 3]), 7)
    expect(out.length).toBe(7)
    expect(Array.from(out)).toEqual([1, 2, 3, 1, 2, 3, 1])
  })

  it('truncates a source longer than the target', () => {
    const out = tileToLength(Float32Array.from([1, 2, 3, 4, 5]), 3)
    expect(Array.from(out)).toEqual([1, 2, 3])
  })

  it('returns silence for an empty source', () => {
    const out = tileToLength(new Float32Array(0), 4)
    expect(Array.from(out)).toEqual([0, 0, 0, 0])
  })
})

describe('overlap: N phase-coded clips summed into one block', () => {
  const clips = FOCALS.map((_, i) => makeClip(1000 + i, i))
  const phi = buildPhaseMask(0x12345, N)
  const block = buildOverlap(clips, FOCALS, phi, AXIS_MAX, ALPHA_MAX)

  it('produces a single block the length of one clip (not N concatenated)', () => {
    expect(block.length).toBe(N)
  })

  it('descrambling at each focal makes that clip the dominant recovered signal', () => {
    FOCALS.forEach((focal, j) => {
      const revealed = phaseTransform(block, phi, -alphaForReveal(focal, AXIS_MAX, ALPHA_MAX))
      const scores = clips.map((c) => Math.abs(corr(revealed, c)))
      const winner = scores.indexOf(Math.max(...scores))
      // the matching clip wins, and is clearly present (well above the noise floor)
      expect(winner).toBe(j)
      expect(scores[j]).toBeGreaterThan(0.45)
      // and clearly dominates each non-matching clip
      scores.forEach((s, i) => { if (i !== j) expect(scores[j]).toBeGreaterThan(s * 2) })
    })
  })
})
