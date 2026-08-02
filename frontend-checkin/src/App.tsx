import { FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import {
  ArrowRight,
  BadgeCheck,
  CalendarDays,
  Check,
  ChevronLeft,
  CircleAlert,
  KeyRound,
  LoaderCircle,
  Mail,
  MapPin,
  ScanLine,
  ShieldCheck,
  Sparkles,
  Users,
} from 'lucide-react'
import { ApiError, checkIn, selectEvent, type CheckinResponse, type EventDetails } from './api'

type View = 'event-code' | 'form' | 'scanning' | 'scan-error' | 'result'

const groupColors: Record<string, string> = {
  Blue: '#4f8cff',
  Red: '#ff6262',
  Orange: '#ff9f43',
  Green: '#4bd18b',
}

function savedEventDetails(): EventDetails | null {
  try {
    const value = sessionStorage.getItem('checkinEvent')
    return value ? JSON.parse(value) as EventDetails : null
  } catch {
    return null
  }
}

function App() {
  const params = useMemo(() => new URLSearchParams(window.location.search), [])
  const barcodeEmail = params.get('email') ?? ''
  const barcodeId = params.get('unique_id') ?? ''
  const barcodeEventCode = params.get('event_code') ?? ''
  const isBarcodeRoute = window.location.pathname.replace(/\/$/, '') === '/checkin-by-barcode'
  const storedEventCode = sessionStorage.getItem('checkinEventCode') ?? ''
  const activeBarcodeEventCode = barcodeEventCode || storedEventCode
  const hasBarcodeCredentials = Boolean(barcodeEmail && barcodeId && activeBarcodeEventCode)
  const scanStarted = useRef(false)
  const [eventCode, setEventCode] = useState(storedEventCode)
  const [eventDetails, setEventDetails] = useState<EventDetails | null>(savedEventDetails)
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(
    isBarcodeRoute && !hasBarcodeCredentials
      ? 'This QR code is incomplete or invalid. Please ask an event host for help.'
      : '',
  )
  const [result, setResult] = useState<CheckinResponse | null>(null)
  const [view, setView] = useState<View>(
    isBarcodeRoute
      ? (hasBarcodeCredentials ? 'scanning' : 'scan-error')
      : (storedEventCode ? 'form' : 'event-code'),
  )

  useEffect(() => {
    if (!isBarcodeRoute || !hasBarcodeCredentials || scanStarted.current) return
    scanStarted.current = true

    void checkIn(barcodeEmail, 'barcode', activeBarcodeEventCode, barcodeId)
      .then((response) => {
        setResult(response)
        setView('result')
      })
      .catch((requestError: unknown) => {
        setError(
          requestError instanceof ApiError
            ? requestError.message
            : 'We could not process this QR code. Please try again.',
        )
        setView('scan-error')
      })
  }, [activeBarcodeEventCode, barcodeEmail, barcodeId, hasBarcodeCredentials, isBarcodeRoute])

  const chooseEvent = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      const selected = await selectEvent(eventCode)
      const normalizedCode = selected.code.toUpperCase()
      sessionStorage.setItem('checkinEventCode', normalizedCode)
      sessionStorage.setItem('checkinEvent', JSON.stringify(selected))
      setEventCode(normalizedCode)
      setEventDetails(selected)
      setView('form')
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : 'Something unexpected happened. Please try again.',
      )
    } finally {
      setLoading(false)
    }
  }

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      const response = await checkIn(email, 'email', eventCode)
      setResult(response)
      setView('result')
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : 'Something unexpected happened. Please try again.',
      )
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setEmail('')
    setResult(null)
    setError('')
    setView('form')
    window.history.replaceState({}, '', '/')
  }

  const changeEvent = () => {
    sessionStorage.removeItem('checkinEventCode')
    sessionStorage.removeItem('checkinEvent')
    setEventCode('')
    setEventDetails(null)
    setEmail('')
    setError('')
    setView('event-code')
  }

  return (
    <main className="page-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <nav className="topbar" aria-label="Main navigation">
        <a className="brand" href="/" aria-label="Gather home">
          <span className="brand-mark"><Sparkles size={19} /></span>
          <span>gather<span className="brand-dot">.</span></span>
        </a>
        <div className="secure-label"><ShieldCheck size={15} /> Secure check-in</div>
      </nav>

      <section className="content-grid">
        <aside className="event-panel">
          {view === 'event-code' ? (
            <>
              <div>
                <div className="eyebrow">Event check-in</div>
                <h1>One booth.<br /><em>Every event.</em></h1>
                <p className="intro">
                  Connect this booth to any event managed by your organization.
                  Enter its private code to load the right guest list and check-in settings.
                </p>
              </div>
              <div className="event-card generic-event-card">
                <div className="date-tile"><KeyRound size={27} /></div>
                <div className="event-copy">
                  <span className="event-kicker">Secure booth access</span>
                  <h2>Have your event code ready</h2>
                  <p><ShieldCheck size={15} /> Event details appear only after verification</p>
                </div>
              </div>
              <div className="attendance"><Users size={18} /><span>Built for fast, organized guest entry</span></div>
            </>
          ) : (
            <>
              <div>
                <div className="eyebrow">Event selected</div>
                <h1>Welcome to<br /><em>{eventDetails?.name ?? 'your event'}.</em></h1>
                <p className="intro">This booth is connected and ready to check in registered guests.</p>
              </div>
              {eventDetails && (
                <div className="event-card">
                  <div className="date-tile">
                    {eventDetails.startsAt ? (
                      <><strong>{new Date(eventDetails.startsAt).getDate()}</strong><span>{new Date(eventDetails.startsAt).toLocaleString('en', { month: 'short' }).toUpperCase()}</span></>
                    ) : <CalendarDays size={27} />}
                  </div>
                  <div className="event-copy">
                    <span className="event-kicker">Active event</span>
                    <h2>{eventDetails.name}</h2>
                    {eventDetails.doorsOpen && <p><CalendarDays size={15} /> Doors open {eventDetails.doorsOpen}</p>}
                    {eventDetails.venue && <p><MapPin size={15} /> {eventDetails.venue}</p>}
                  </div>
                </div>
              )}
            </>
          )}
        </aside>

        <section className="checkin-card" aria-live="polite">
          {view === 'event-code' ? (
            <>
              <header className="card-header">
                <span className="step-label">BOOTH SETUP · STEP 1 OF 1</span>
                <h2>Enter event code</h2>
                <p>Connect this check-in booth to an event.</p>
              </header>

              <form onSubmit={chooseEvent} className="event-code-form">
                <label htmlFor="eventCode">Event code</label>
                <div className="input-wrap">
                  <KeyRound size={18} />
                  <input
                    id="eventCode"
                    value={eventCode}
                    onChange={(event) => setEventCode(event.target.value.toUpperCase())}
                    placeholder="e.g. GATHER2026"
                    autoComplete="off"
                    spellCheck="false"
                    required
                    autoFocus
                  />
                </div>
                <span className="field-help">Ask your event organizer for the booth code.</span>

                {error && <div className="error-banner"><CircleAlert size={18} /><span>{error}</span></div>}

                <button className="primary-button" disabled={loading} type="submit">
                  {loading ? <><LoaderCircle className="spinner" size={19} /> Finding event…</> : <>Continue <ArrowRight size={19} /></>}
                </button>
              </form>

              <p className="privacy-note"><ShieldCheck size={14} /> Authorized event staff only.</p>
            </>
          ) : view === 'form' ? (
            <>
              <header className="card-header">
                <div className="selected-event">
                  <span className="step-label">{eventDetails?.name ?? 'EVENT SELECTED'}</span>
                  <button type="button" onClick={changeEvent}>Change event</button>
                </div>
                <h2>Find your invitation</h2>
                <p>Enter the email address on your invitation.</p>
              </header>

              <form onSubmit={submit}>
                <label htmlFor="email">Email address</label>
                <div className="input-wrap">
                  <Mail size={18} />
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="you@example.com"
                    autoComplete="email"
                    required
                  />
                </div>

                {error && <div className="error-banner"><CircleAlert size={18} /><span>{error}</span></div>}

                <button className="primary-button" disabled={loading} type="submit">
                  {loading ? <><LoaderCircle className="spinner" size={19} /> Checking your details…</> : <>Check me in <ArrowRight size={19} /></>}
                </button>
              </form>

              <p className="privacy-note"><ShieldCheck size={14} /> Your information is encrypted and used only for this event.</p>
            </>
          ) : view === 'scanning' ? (
            <div className="scan-view">
              <div className="scan-icon"><ScanLine size={34} /><span /></div>
              <span className="step-label">QR CHECK-IN</span>
              <h2>Checking you in…</h2>
              <p>Hold tight while we verify your invitation.</p>
            </div>
          ) : view === 'scan-error' ? (
            <div className="scan-view scan-failed">
              <div className="scan-error-icon"><CircleAlert size={34} /></div>
              <span className="step-label">CHECK-IN UNSUCCESSFUL</span>
              <h2>We couldn’t check you in</h2>
              <p>{error}</p>
              <button className="secondary-button" type="button" onClick={reset}>
                <ChevronLeft size={18} /> Use email instead
              </button>
            </div>
          ) : result && (
            <div className="result-view">
              <div className={`success-icon ${result.status === 'already_checked_in' ? 'repeat' : ''}`}>
                {result.status === 'checked_in' ? <Check size={38} /> : <BadgeCheck size={38} />}
              </div>
              <span className="step-label">
                {result.status === 'checked_in' ? 'YOU’RE ALL SET' : 'WELCOME BACK'}
              </span>
              <h2>{result.status === 'checked_in' ? `Welcome, ${result.guest.name.split(' ')[0]}!` : 'Already checked in'}</h2>
              <p className="result-copy">
                {result.status === 'checked_in'
                  ? 'Your place is confirmed. Show this screen to a host and head on in.'
                  : `${result.guest.name} has already completed check-in.`}
              </p>

              <div className="guest-pass">
                <div className="pass-topline"><span>GUEST PASS</span><ScanLine size={22} /></div>
                {result.displayFields.includes('name') && <strong>{result.guest.name}</strong>}
                {result.displayFields.includes('email') && <span>{result.guest.email}</span>}
                <div className="pass-footer">
                  {result.displayFields.includes('uniqueId') && <span>ID · {result.guest.uniqueId}</span>}
                  {result.displayFields.includes('tier') && result.guest.group && (
                    <span className="group-chip" style={{ '--group-color': groupColors[result.guest.group] ?? '#d6ff50' } as React.CSSProperties}>
                      <i /> {result.guest.group} group
                    </span>
                  )}
                </div>
                {result.displayFields.includes('checkedInAt') && result.guest.checkedInAt && <div className="checkin-time"><span>CHECKED IN</span><strong>{new Intl.DateTimeFormat(undefined,{dateStyle:'medium',timeStyle:'short'}).format(new Date(result.guest.checkedInAt))}</strong></div>}
              </div>

              <button className="secondary-button" type="button" onClick={reset}>
                <ChevronLeft size={18} /> Check in another guest
              </button>
            </div>
          )}
        </section>
      </section>

      <footer><span>© 2026 Gather Events</span><span>Need help? Find a host in a green lanyard.</span></footer>
    </main>
  )
}

export default App
