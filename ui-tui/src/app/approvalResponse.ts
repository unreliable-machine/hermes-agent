import type { ApprovalRespondResponse } from '../gatewayTypes.js'

/** Only the backend's exact single-request resolution is consent. */
export const approvalResponseResolved = (response: ApprovalRespondResponse | null | undefined): boolean =>
  response?.resolved === 1
