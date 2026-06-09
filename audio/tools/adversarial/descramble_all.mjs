// tools/adversarial/descramble_all.mjs  (offline verification, never shipped)
// Simulates the attacker: for each focal, descramble the asset with the SHIPPED
// math and pick the resolving block (highest kurtosis), then write it to a wav so
// verify.py can transcribe what Whisper-tiny would actually see. This is the true
// end-to-end path: perturb -> scramble -> 16-bit -> descramble -> (resample) -> STT.
import { readWavMono, writeWavMono } from '../wav.mjs'
import { buildPhaseMask, alphaForReveal, rotatePhase } from '../../src/scramble.js'
import { transform } from '../../src/fft.js'
import { AXIS_MAX, ASSET_RATE, BLOCK_LEN, PHASE_SEED, ALPHA_MAX } from '../../src/constants.js'

const FOCALS = [60, 160, 250, 360, 460, 560, 650, 760, 850, 950]

const { samples } = readWavMono('public/assets/message.wav')
const blocks = Math.floor(samples.length / BLOCK_LEN)
const phi = buildPhaseMask(PHASE_SEED, BLOCK_LEN)

const reG = []
const imG = []
for (let b = 0; b < blocks; b++) {
  const re = new Float64Array(BLOCK_LEN)
  const im = new Float64Array(BLOCK_LEN)
  for (let i = 0; i < BLOCK_LEN; i++) re[i] = samples[b * BLOCK_LEN + i]
  transform(re, im, false)
  reG.push(re)
  imG.push(im)
}

function kurtosis(a) {
  let m = 0
  for (const x of a) m += x
  m /= a.length
  let m2 = 0
  let m4 = 0
  for (const x of a) {
    const d = x - m
    m2 += d * d
    m4 += d * d * d * d
  }
  m2 /= a.length
  m4 /= a.length
  return m2 > 0 ? m4 / (m2 * m2) : 0
}

for (const focal of FOCALS) {
  const alpha = alphaForReveal(focal, AXIS_MAX, ALPHA_MAX)
  let bestK = -Infinity
  let best = null
  for (let b = 0; b < blocks; b++) {
    const re = reG[b].slice()
    const im = imG[b].slice()
    rotatePhase(re, im, phi, -alpha)
    transform(re, im, true)
    const out = new Float32Array(BLOCK_LEN)
    for (let i = 0; i < BLOCK_LEN; i++) out[i] = re[i]
    const k = kurtosis(out)
    if (k > bestK) {
      bestK = k
      best = out
    }
  }
  writeWavMono(`tools/adversarial/verify_${focal}.wav`, best, ASSET_RATE)
}
console.log('wrote verify_*.wav for focals', FOCALS.join(', '))
