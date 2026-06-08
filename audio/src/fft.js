// src/fft.js
// In-place iterative radix-2 Cooley-Tukey FFT. Length must be a power of two.
// re and im are equal-length Float64Array; the transform overwrites them.
// inverse=true computes the inverse transform and divides by N.
export function isPow2(n) {
  return n > 0 && (n & (n - 1)) === 0
}

export function transform(re, im, inverse = false) {
  const n = re.length
  if (!isPow2(n)) throw new RangeError(`FFT length must be a power of two, got ${n}`)
  if (im.length !== n) throw new RangeError('re and im must be the same length')

  // Bit-reversal permutation.
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1
    for (; j & bit; bit >>= 1) j ^= bit
    j ^= bit
    if (i < j) {
      const tr = re[i]; re[i] = re[j]; re[j] = tr
      const ti = im[i]; im[i] = im[j]; im[j] = ti
    }
  }

  // Butterflies.
  for (let len = 2; len <= n; len <<= 1) {
    const ang = ((inverse ? 2 : -2) * Math.PI) / len
    const wr = Math.cos(ang)
    const wi = Math.sin(ang)
    const half = len >> 1
    for (let i = 0; i < n; i += len) {
      let cwr = 1
      let cwi = 0
      for (let k = 0; k < half; k++) {
        const a = i + k
        const b = a + half
        const vr = re[b] * cwr - im[b] * cwi
        const vi = re[b] * cwi + im[b] * cwr
        re[b] = re[a] - vr
        im[b] = im[a] - vi
        re[a] = re[a] + vr
        im[a] = im[a] + vi
        const ncwr = cwr * wr - cwi * wi
        cwi = cwr * wi + cwi * wr
        cwr = ncwr
      }
    }
  }

  if (inverse) {
    for (let i = 0; i < n; i++) {
      re[i] /= n
      im[i] /= n
    }
  }
}
