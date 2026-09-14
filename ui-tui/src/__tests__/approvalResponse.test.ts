import { describe, expect, it, vi } from 'vitest'

import { approvalResponseResolved } from '../app/approvalResponse.js'
import { getOverlayState, patchOverlayState, resetOverlayState } from '../app/overlayStore.js'
import { getTurnState, resetTurnState } from '../app/turnStore.js'
import { denyApprovalFromCtrlC } from '../app/useInputHandlers.js'
import { answerApprovalRequest } from '../app/useMainApp.js'

describe('approvalResponseResolved', () => {
  it('accepts only the backend exact-request resolution count', () => {
    expect(approvalResponseResolved({ resolved: 1 })).toBe(true)
    expect(approvalResponseResolved({ resolved: 0 })).toBe(false)
    expect(approvalResponseResolved({ resolved: 2 })).toBe(false)
    expect(approvalResponseResolved(undefined)).toBe(false)
  })
})

describe('approval response handlers', () => {
  it('explicit choice retains a wrong or expired request and reports failure', async () => {
    resetOverlayState()
    resetTurnState()
    patchOverlayState({
      approval: {
        choices: ['once', 'deny'],
        command: 'test',
        description: 'protected action',
        requestId: 'expired-explicit'
      }
    })
    const rpc = vi.fn().mockResolvedValue({ resolved: 0 })
    const sys = vi.fn()

    await answerApprovalRequest(rpc, 'once', 'expired-explicit', 'session-1', sys)

    expect(rpc).toHaveBeenCalledWith('approval.respond', {
      choice: 'once',
      request_id: 'expired-explicit',
      session_id: 'session-1'
    })
    expect(getOverlayState().approval?.requestId).toBe('expired-explicit')
    expect(getTurnState().outcome).toBe('')
    expect(sys).toHaveBeenCalledWith(expect.stringContaining('not resolved'))
  })

  it('Ctrl-C deny retains a wrong or expired request and reports failure', async () => {
    resetOverlayState()
    resetTurnState()
    patchOverlayState({
      approval: {
        choices: ['once', 'deny'],
        command: 'test',
        description: 'protected action',
        requestId: 'expired-deny'
      }
    })
    const rpc = vi.fn().mockResolvedValue({ resolved: 0 })
    const sys = vi.fn()

    await denyApprovalFromCtrlC(rpc, 'expired-deny', 'session-1', sys)

    expect(rpc).toHaveBeenCalledWith('approval.respond', {
      choice: 'deny',
      request_id: 'expired-deny',
      session_id: 'session-1'
    })
    expect(getOverlayState().approval?.requestId).toBe('expired-deny')
    expect(getTurnState().outcome).toBe('')
    expect(sys).toHaveBeenCalledWith(expect.stringContaining('not resolved'))
  })
})
