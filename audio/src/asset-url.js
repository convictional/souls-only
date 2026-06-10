// src/asset-url.js
// Resolve which asset the demo loads. The shipped asset is the 3-channel overlap
// (message.wav); ?asset=<name> can point at another file in /assets. The name is
// reduced to a safe basename so it cannot point outside the assets directory.
const DEFAULT_ASSET = 'message.wav'

export function assetUrl(search) {
  const raw = new URLSearchParams(search).get('asset') || DEFAULT_ASSET
  const name = raw.replace(/[^a-zA-Z0-9._-]/g, '')
  return '/assets/' + (name || DEFAULT_ASSET)
}
