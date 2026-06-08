// src/constants.js
// Shared dial and asset constants. AXIS_MAX is the slider range; ASSET_RATE is
// the sample rate the garbled asset is produced at and the AudioContext must
// run at, so the runtime FFT stays sample-aligned with the asset.
//
// These live here (not in reveal-engine.js) so the offline garble tool can
// import them without pulling in reveal-engine.js, which imports the worklet via
// a `?url` specifier that plain Node cannot load. The focal value is NOT here:
// the dial maps linearly to a phase-rotation amount, and the scramble only
// cancels where that amount matches the one baked into the asset offline.
export const AXIS_MAX = 1000
export const ASSET_RATE = 22050

// Per-station block length in samples. A power of two so each block's FFT is
// exact. About 3 seconds at 22050, sized to hold the spoken message.
export const BLOCK_LEN = 65536

// Number of stations the asset carries. One is the real message; the rest are
// babble decoys (tools/babble.mjs) — the real message's own frames reordered, so
// they share its kurtosis AND its energy-envelope CV exactly. Each station is
// phase-scrambled at its own focal rotation, so a statistics sweep (kurtosis,
// envelope CV) lights up at every station identically and cannot pick the real
// one; only recognizing actual words (a human, or STT) distinguishes it. Which
// focal is the real message lives offline in tools/garble.mjs, never here.
export const STATIONS = 4

// Public seed for the per-bin phase mask. Knowing it does not reveal the focal
// point: recovering that still requires rendering the audio and judging it.
export const PHASE_SEED = 0x85ebca6b

// The dial 0..AXIS_MAX maps linearly to a phase-rotation amount 0..ALPHA_MAX.
// Larger ALPHA_MAX means more total scramble across the dial and a narrower
// clear region. Tune by ear.
export const ALPHA_MAX = 4
