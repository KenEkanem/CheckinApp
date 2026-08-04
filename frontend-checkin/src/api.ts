export type CheckinMethod = 'email' | 'barcode'

export interface Guest {
  name: string
  email: string
  uniqueId: string
  group: string | null
  checkedInAt: string | null
}

export interface CheckinResponse {
  status: 'checked_in' | 'already_checked_in'
  guest: Guest
  displayFields: Array<'name' | 'email' | 'uniqueId' | 'tier' | 'checkedInAt'>
}

export interface EventDetails {
  name: string
  code: string
  checkinOpen: boolean
  startsAt: string | null
  venue: string | null
  doorsOpen: string | null
}

interface ApiErrorBody {
  error?: { code?: string; message?: string }
}

const configuredUrl = import.meta.env.VITE_API_URL as string | undefined
const API_URL = configuredUrl?.replace(/\/$/, '') ?? '/api'

export class ApiError extends Error {
  code: string

  constructor(message: string, code = 'UNKNOWN_ERROR') {
    super(message)
    this.name = 'ApiError'
    this.code = code
  }
}

export async function checkIn(
  email: string,
  method: CheckinMethod,
  eventCode: string,
  uniqueId?: string,
): Promise<CheckinResponse> {
  let response: Response
  try {
    response = await fetch(`${API_URL}/check-ins`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, method, eventCode, uniqueId }),
    })
  } catch {
    throw new ApiError(
      'We could not reach the check-in service. Check your connection and try again.',
      'NETWORK_ERROR',
    )
  }

  const body = (await response.json().catch(() => ({}))) as ApiErrorBody
  if (!response.ok) {
    throw new ApiError(
      body.error?.message ?? 'Something went wrong. Please try again.',
      body.error?.code,
    )
  }
  return body as CheckinResponse
}

export async function selectEvent(eventCode: string): Promise<EventDetails> {
  let response: Response
  try {
    response = await fetch(`${API_URL}/events/select`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ eventCode }),
    })
  } catch {
    throw new ApiError(
      'We could not reach the event service. Check your connection and try again.',
      'NETWORK_ERROR',
    )
  }

  const body = (await response.json().catch(() => ({}))) as ApiErrorBody & { event?: EventDetails }
  if (!response.ok || !body.event) {
    throw new ApiError(
      body.error?.message ?? 'We could not find that event.',
      body.error?.code,
    )
  }
  return body.event
}
