// src/scramble.js
// Spectral phase scrambling: a fundamental, invertible transform that destroys
// intelligibility without adding noise. It rotates each frequency bin's phase
// by alpha*phi[k] while leaving magnitude untouched, so the garbled signal has
// the same spectral energy as the clean one but no temporal structure (no
// words). Descrambling rotates by the opposite amount. The focal value lives
// only in how much the asset was pre-rotated; this code maps the dial to alpha
// linearly and contains no focal value.
import { mulberry32 } from './rng.js'
import { transform } from './fft.js'

// Per-bin phase offsets in [-PI, PI), deterministic per seed. Built conjugate-
// symmetric (phi[N-k] = -phi[k], phi[0] = phi[N/2] = 0) so the inverse transform
// of a phase-rotated real signal stays real.
export function buildPhaseMask(seed, n) {
  const phi = new Float64Array(n)
  const rng = mulberry32(seed)
  for (let k = 1; k < n / 2; k++) {
    const v = (rng() * 2 - 1) * Math.PI
    phi[k] = v
    phi[n - k] = -v
  }
  return phi
}

// Linear dial -> phase-rotation amount. No special point; the focal location is
// baked into the asset, not derivable from this map.
export function alphaForReveal(revl, axisMax, alphaMax) {
  const v = Math.max(0, Math.min(axisMax, revl))
  return (v / axisMax) * alphaMax
}

// Rotate a spectrum's phase by alpha*phi per bin, in place: bin *= e^{i*alpha*phi[k]}.
export function rotatePhase(re, im, phi, alpha) {
  const n = re.length
  for (let k = 0; k < n; k++) {
    const t = alpha * phi[k]
    const c = Math.cos(t)
    const s = Math.sin(t)
    const r = re[k]
    const i = im[k]
    re[k] = r * c - i * s
    im[k] = r * s + i * c
  }
}

// Phase-transform a real signal by +alpha*phi: forward FFT, rotate, inverse FFT,
// return the real part. Used offline to garble (alpha > 0) and in tests. The
// length must be a power of two.
export function phaseTransform(signal, phi, alpha) {
  const n = signal.length
  const re = new Float64Array(n)
  const im = new Float64Array(n)
  for (let i = 0; i < n; i++) re[i] = signal[i]
  transform(re, im, false)
  rotatePhase(re, im, phi, alpha)
  transform(re, im, true)
  const out = new Float32Array(n)
  for (let i = 0; i < n; i++) out[i] = re[i]
  return out
}
