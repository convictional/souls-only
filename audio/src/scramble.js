// src/scramble.js
// Per-bin phase rotation in the frequency domain. rotatePhase multiplies bin k by
// e^{i*alpha*phi[k]} (magnitude unchanged); the inverse rotation uses -alpha.
// phaseTransform applies it to a real signal via FFT. Invertible, energy-preserving.
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

// Linear map from the control value to a phase-rotation amount.
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

// Apply +alpha*phi to a real signal: forward FFT, rotate, inverse FFT, return the
// real part. The length must be a power of two.
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
