// tools/babble.mjs
// Offline: turn the real clip into a "babble" decoy by re-ordering its own short
// frames in time. Because it is a pure permutation of the signal's frames, the
// decoy carries the EXACT same multiset of samples as the real clip (identical
// amplitude histogram → identical kurtosis) AND the same multiset of short-time
// frame energies (identical energy-envelope coefficient of variation). So the
// two metrics an attacker has used to locate the focal — kurtosis and envelope
// CV — read identically at a decoy station and at the real one. Only the
// word-order/temporal structure is destroyed, so a human ear (or STT) can tell
// real words from babble, but a statistics sweep cannot. Node-only; never
// shipped to the browser.
import { mulberry32 } from '../src/rng.js'

// Re-order the `frameLen`-sample frames of `signal` with a seeded permutation.
// Any trailing partial frame (when length is not a multiple of frameLen) is left
// in place at the end. The output is the same length and the same sample
// multiset (exactly, when length divides evenly into frames).
export function frameShuffle(signal, seed, frameLen) {
  const n = signal.length
  const frameCount = Math.floor(n / frameLen)
  const order = new Array(frameCount)
  for (let i = 0; i < frameCount; i++) order[i] = i

  // Fisher-Yates with the seeded RNG, so each decoy is deterministic per seed.
  const rng = mulberry32(seed)
  for (let i = frameCount - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1))
    const t = order[i]
    order[i] = order[j]
    order[j] = t
  }

  const out = new Float32Array(n)
  for (let dst = 0; dst < frameCount; dst++) {
    const src = order[dst]
    out.set(signal.subarray(src * frameLen, (src + 1) * frameLen), dst * frameLen)
  }
  // Copy any trailing partial frame unchanged.
  if (frameCount * frameLen < n) {
    out.set(signal.subarray(frameCount * frameLen, n), frameCount * frameLen)
  }
  return out
}
