// tools/garble.mjs
// Offline: produce the phase-scrambled public/assets/message.wav. This is the
// ONLY place the focal value lives. Run with: node tools/garble.mjs
// macOS only (uses `say` to synthesize the clean voice transiently in /tmp;
// the clean audio is never committed or shipped).
import { execFileSync } from 'node:child_process'
import { rmSync } from 'node:fs'
import { readWavMono, writeWavMono } from './wav.mjs'
import { buildPhaseMask, alphaForReveal, phaseTransform } from '../src/scramble.js'
// Read constants from constants.js, not reveal-engine.js: the latter imports the
// worklet via a `?url` specifier that plain Node cannot load.
import { AXIS_MAX, ASSET_RATE, ASSET_LEN, PHASE_SEED, ALPHA_MAX } from '../src/constants.js'

// The hidden focal value. Lives here, never in shipped code.
const FOCAL = 650

const PHRASE = 'This is a souls only audio message.'
const TMP_AIFF = '/tmp/soa-clean.aiff'
const TMP_WAV = '/tmp/soa-clean.wav'
const OUT = 'public/assets/message.wav'

// 1. Synthesize the clean voice at the asset rate, transiently.
execFileSync('say', ['-o', TMP_AIFF, PHRASE])
execFileSync('afconvert', ['-f', 'WAVE', '-d', `LEI16@${ASSET_RATE}`, '-c', '1', TMP_AIFF, TMP_WAV])

try {
  // 2. Read clean samples.
  const { sampleRate, samples: clean } = readWavMono(TMP_WAV)
  if (sampleRate !== ASSET_RATE) {
    throw new Error(`clean rate ${sampleRate} != ASSET_RATE ${ASSET_RATE}`)
  }
  if (clean.length > ASSET_LEN) {
    throw new Error(`clean is ${clean.length} samples, longer than ASSET_LEN ${ASSET_LEN}; shorten the phrase or raise ASSET_LEN`)
  }

  // 3. Pad to the power-of-two asset length so the whole-buffer FFT is exact and
  // the looping signal is one circular block.
  const padded = new Float32Array(ASSET_LEN)
  padded.set(clean)

  // 4. Phase-scramble at the focal rotation amount. The voice is destroyed (phase
  // randomized, magnitude preserved); only descrambling at this same amount in
  // the runtime brings it back.
  const phi = buildPhaseMask(PHASE_SEED, ASSET_LEN)
  const alphaFocal = alphaForReveal(FOCAL, AXIS_MAX, ALPHA_MAX)
  const garbled = phaseTransform(padded, phi, alphaFocal)

  // 5. Write the garbled asset.
  writeWavMono(OUT, garbled, ASSET_RATE)
  console.log(`wrote ${OUT}: ${ASSET_LEN} samples at ${ASSET_RATE} Hz, scrambled at focal alpha ${alphaFocal}`)
} finally {
  // Always remove the transient clean audio.
  rmSync(TMP_AIFF, { force: true })
  rmSync(TMP_WAV, { force: true })
}
