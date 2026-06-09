// src/asset-url.js
// Resolve which asset the demo loads. ?asset=<name> selects a file in /assets
// (e.g. the code-division overlap experiment, overlap-3.wav); the default is the
// shipped ten-station file. The name is reduced to a safe basename so it cannot
// point outside the assets directory.
export function assetUrl(search) {
  const raw = new URLSearchParams(search).get('asset') || 'message.wav'
  const name = raw.replace(/[^a-zA-Z0-9._-]/g, '')
  return '/assets/' + (name || 'message.wav')
}
