// src/asset-url.js
import { BLOCK_LEN, OVERLAP_BLOCK_LEN } from './constants.js'

// The main method is the 3-channel code-division overlap, so it is the default
// asset. ?asset=<name> selects another file in /assets (e.g. the legacy
// ten-station message.wav). The name is reduced to a safe basename so it cannot
// point outside the assets directory.
const DEFAULT_ASSET = 'overlap-3.wav'

export function assetUrl(search) {
  const raw = new URLSearchParams(search).get('asset') || DEFAULT_ASSET
  const name = raw.replace(/[^a-zA-Z0-9._-]/g, '')
  return '/assets/' + (name || DEFAULT_ASSET)
}

// The block length the engine must descramble at for the chosen asset. The overlap
// packs all channels into one long block, so it needs the larger OVERLAP_BLOCK_LEN;
// the legacy ten-station file uses the standard BLOCK_LEN.
export function assetBlockLen(search) {
  const name = (new URLSearchParams(search).get('asset') || DEFAULT_ASSET).toLowerCase()
  return name.includes('overlap') ? OVERLAP_BLOCK_LEN : BLOCK_LEN
}
