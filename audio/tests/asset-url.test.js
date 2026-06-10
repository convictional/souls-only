// tests/asset-url.test.js
// Resolve which asset the demo loads from the page's query string. Defaults to the
// shipped file; ?asset= picks another file in /assets, basename-only (no path
// traversal out of the assets directory).
import { describe, it, expect } from 'vitest'
import { assetUrl, assetBlockLen } from '../src/asset-url.js'
import { BLOCK_LEN, OVERLAP_BLOCK_LEN } from '../src/constants.js'

describe('assetUrl', () => {
  it('defaults to the shipped ten-station asset', () => {
    expect(assetUrl('')).toBe('/assets/message.wav')
  })

  it('loads an alternate asset named in ?asset=', () => {
    expect(assetUrl('?asset=overlap-3.wav')).toBe('/assets/overlap-3.wav')
  })

  it('falls back to the default when ?asset= is empty', () => {
    expect(assetUrl('?asset=')).toBe('/assets/message.wav')
  })

  it('strips path separators so it cannot escape /assets', () => {
    expect(assetUrl('?asset=../../secret.wav')).toBe('/assets/....secret.wav')
    expect(assetUrl('?asset=/etc/passwd')).not.toContain('/etc/')
  })
})

describe('assetBlockLen', () => {
  it('uses the standard block length by default', () => {
    expect(assetBlockLen('')).toBe(BLOCK_LEN)
    expect(assetBlockLen('?asset=message.wav')).toBe(BLOCK_LEN)
  })

  it('uses the longer overlap block length for an overlap asset', () => {
    expect(assetBlockLen('?asset=overlap-3.wav')).toBe(OVERLAP_BLOCK_LEN)
  })
})
