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

// Asset length in samples. A power of two so the whole-buffer FFT is exact and
// the looping signal is treated as one circular block. About 3 seconds at 22050.
export const ASSET_LEN = 65536

// Public seed for the per-bin phase mask. Knowing it does not reveal the focal
// point: recovering that still requires rendering the audio and judging it.
export const PHASE_SEED = 0x85ebca6b

// The dial 0..AXIS_MAX maps linearly to a phase-rotation amount 0..ALPHA_MAX.
// Larger ALPHA_MAX means more total scramble across the dial and a narrower
// clear region. Tune by ear.
export const ALPHA_MAX = 4
