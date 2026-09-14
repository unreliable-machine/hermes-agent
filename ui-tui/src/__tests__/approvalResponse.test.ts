import { describe, expect, it } from 'vitest'

import { approvalResponseResolved } from '../app/approvalResponse.js'

describe('approvalResponseResolved', () => {
  it('accepts only the backend exact-request resolution count', () => {
    expect(approvalResponseResolved({ resolved: 1 })).toBe(true)
    expect(approvalResponseResolved({ resolved: 0 })).toBe(false)
    expect(approvalResponseResolved({ resolved: 2 })).toBe(false)
    expect(approvalResponseResolved(undefined)).toBe(false)
  })
})
