// tools/overlap.mjs
// Code-division (overlap) variant of the asset layout. Instead of concatenating
// N stations in time, sum N phase-coded clips into ONE block the length of a
// single clip. Each clip is phase-rotated at its own focal; the sum is a block in
// which descrambling at focal j (the runtime's -alpha rotation) reconstructs clip
// j exactly, while every other clip stays rotated and remains additive noise.
import { phaseTransform, alphaForReveal } from '../src/scramble.js'

// clips: array of equal-length real Float32Arrays. focals: matching dial values.
// Returns one Float32Array of the same length as a single clip.
export function buildOverlap(clips, focals, phi, axisMax, alphaMax) {
  const n = clips[0].length
  const out = new Float32Array(n)
  for (let i = 0; i < clips.length; i++) {
    const coded = phaseTransform(clips[i], phi, alphaForReveal(focals[i], axisMax, alphaMax))
    for (let k = 0; k < n; k++) out[k] += coded[k]
  }
  return out
}
