import { describe, expect, it } from 'vitest'

import { formatMw, formatPct, formatSignedMw } from './format'

describe('numeric formatting', () => {
  it('formats megawatts with a dash for missing values', () => {
    expect(formatMw(12345.6, 0)).toBe('12,346')
    expect(formatMw(null)).toBe('—')
  })

  it('formats signed errors without treating missing as zero', () => {
    expect(formatSignedMw(250)).toBe('+250')
    expect(formatSignedMw(-90)).toBe('−90')
    expect(formatSignedMw(undefined)).toBe('—')
  })

  it('formats percentages', () => {
    expect(formatPct(12.345, 1)).toBe('12.3%')
    expect(formatPct(null)).toBe('—')
  })
})
