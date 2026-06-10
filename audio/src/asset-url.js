// src/asset-url.js
import { BLOCK_LEN, OVERLAP_BLOCK_LEN } from './constants.js'
// Resolve which asset the demo loads. ?asset=<name> selects a file in /assets
// (e.g. the code-division overlap experiment, overlap-3.wav); the default is the
// shipped ten-station file. The name is reduced to a safe basename so it cannot
// point outside the assets directory.
export function assetUrl(search) {
  const raw = new URLSearchParams(search).get('asset') || 'message.wav'
  const name = raw.replace(/[^a-zA-Z0-9._-]/g, '')
  return '/assets/' + (name || 'message.wav')
}

// The block length the engine must descramble at for the chosen asset. The
// overlap experiment packs all stations into one long block, so it needs the
// larger OVERLAP_BLOCK_LEN; everything else uses the standard BLOCK_LEN.
export function assetBlockLen(search) {
  const name = (new URLSearchParams(search).get('asset') || '').toLowerCase()
  return name.includes('overlap') ? OVERLAP_BLOCK_LEN : BLOCK_LEN
}
