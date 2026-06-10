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
// Block length for the code-division overlap experiment (feat/overlap-stations):
// one block holds all overlapped stations, so it must fit the longest clip. 2^20
// samples is ~47.5s at ASSET_RATE (a power of two for the radix-2 FFT).
export const OVERLAP_BLOCK_LEN = 1 << 20
