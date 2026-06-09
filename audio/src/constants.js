// src/constants.js
// Runtime constants shared by the engine. AXIS_MAX is the control range. The
// AudioContext must run at ASSET_RATE so the per-bin transform stays sample-aligned
// with the asset. BLOCK_LEN is the per-segment FFT length (a power of two, ~3s at
// ASSET_RATE). PHASE_SEED and ALPHA_MAX parameterize the per-bin phase transform.
export const AXIS_MAX = 1000
export const ASSET_RATE = 22050
export const BLOCK_LEN = 65536
export const PHASE_SEED = 0x85ebca6b
export const ALPHA_MAX = 10
