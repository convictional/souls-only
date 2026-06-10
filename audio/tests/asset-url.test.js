// tests/asset-url.test.js
// Resolve which asset the demo loads from the page's query string. The main method
// is now the 3-channel overlap, so that is the default; ?asset= picks another file
// in /assets (e.g. the legacy ten-station message.wav), basename-only (no path
// traversal out of the assets directory).
import { describe, it, expect } from 'vitest'
import { assetUrl, assetBlockLen } from '../src/asset-url.js'
import { BLOCK_LEN, OVERLAP_BLOCK_LEN } from '../src/constants.js'

describe('assetUrl', () => {
  it('defaults to the 3-channel overlap (the main method)', () => {
    expect(assetUrl('')).toBe('/assets/overlap-3.wav')
  })

  it('loads an alternate asset named in ?asset= (e.g. the legacy build)', () => {
    expect(assetUrl('?asset=message.wav')).toBe('/assets/message.wav')
  })

  it('falls back to the default when ?asset= is empty', () => {
    expect(assetUrl('?asset=')).toBe('/assets/overlap-3.wav')
  })

  it('strips path separators so it cannot escape /assets', () => {
    expect(assetUrl('?asset=../../secret.wav')).toBe('/assets/....secret.wav')
    expect(assetUrl('?asset=/etc/passwd')).not.toContain('/etc/')
  })
})

describe('assetBlockLen', () => {
  it('uses the longer overlap block length by default (overlap is the main method)', () => {
    expect(assetBlockLen('')).toBe(OVERLAP_BLOCK_LEN)
    expect(assetBlockLen('?asset=overlap-3.wav')).toBe(OVERLAP_BLOCK_LEN)
  })

  it('uses the standard block length for the legacy ten-station asset', () => {
    expect(assetBlockLen('?asset=message.wav')).toBe(BLOCK_LEN)
  })
})
