import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api'
import type { PublicEvite } from '../types'

export default function EvitePublic() {
  const { uuid } = useParams()
  const [evite, setEvite] = useState<PublicEvite | null>(null)
  const [notFound, setNotFound] = useState(false)
  const [rsvpMsg, setRsvpMsg] = useState('')
  const [count, setCount] = useState(1)
  const [otpSent, setOtpSent] = useState(false)
  const [otp, setOtp] = useState('')
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)

  const load = () =>
    api.get(`/public/evite/${uuid}`)
      .then((r) => { setEvite(r.data); setCount(r.data.admits) })
      .catch(() => setNotFound(true))
  useEffect(() => { load() }, [uuid])

  async function rsvp(status: 'attending' | 'declined') {
    await api.post(`/public/evite/${uuid}/rsvp`, {
      status, count: status === 'attending' ? count : 0,
    })
    setRsvpMsg(status === 'attending'
      ? 'See you there!' : 'Sorry to miss you — response recorded.')
    load()
  }

  async function requestOtp() {
    setBusy(true)
    const r = await api.post(`/public/evite/${uuid}/otp/request`)
    setMsg(r.data.detail)
    setOtpSent(true)
    setBusy(false)
  }

  async function verifyOtp() {
    setBusy(true)
    try {
      const r = await api.post(`/public/evite/${uuid}/otp/verify`, { code: otp })
      setMsg(r.data.detail)
      load()
    } catch (e: any) {
      setMsg(e.response?.data?.detail ?? 'Verification failed')
    } finally { setBusy(false) }
  }

  async function admit() {
    if (!evite) return
    await api.post(`/events/${evite.event.id}/guests/${uuid}/admit`)
    load()
  }

  if (notFound) {
    return <Shell><p className="text-center text-slate-500">
      This invitation could not be found.</p></Shell>
  }
  if (!evite) return <Shell><p className="text-center text-slate-500">Loading…</p></Shell>

  return (
    <Shell>
      <div className="card p-6 text-center">
        {evite.attended && (
          <div className="mb-4 rounded-xl bg-green-50 py-2 text-sm font-bold text-green-700">
            ✓ This invitation has been verified / admitted
          </div>
        )}
        <p className="text-xs uppercase tracking-widest text-slate-400">
          You are invited to
        </p>
        <h1 className="mt-1 text-2xl font-extrabold text-[#10233f]">
          {evite.event.name}
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          {evite.event.date_text}<br />
          {evite.event.venue}<br />
          {evite.event.dress_code && <>Dress code: {evite.event.dress_code}</>}
        </p>
        <p className="mt-3 font-semibold text-[#0b5cff]">
          {evite.title} {evite.name} · admits {evite.admits}
        </p>

        {/* RSVP */}
        <div className="mt-5 border-t border-slate-100 pt-5">
          <p className="label">RSVP</p>
          {evite.rsvp_status === 'pending' ? (
            <>
              <div className="mb-3 flex items-center justify-center gap-2">
                <span className="text-sm text-slate-500">Guests coming:</span>
                <select className="input w-20" value={count}
                        onChange={(e) => setCount(Number(e.target.value))}>
                  {Array.from({ length: evite.admits }, (_, i) => i + 1)
                    .map((n) => <option key={n}>{n}</option>)}
                </select>
              </div>
              <div className="flex justify-center gap-2">
                <button className="btn" onClick={() => rsvp('attending')}>
                  Attending
                </button>
                <button className="btn-outline" onClick={() => rsvp('declined')}>
                  Can't make it
                </button>
              </div>
            </>
          ) : (
            <p className="text-sm">
              RSVP: <b className={evite.rsvp_status === 'attending'
                ? 'text-green-600' : 'text-red-500'}>
                {evite.rsvp_status}
                {evite.rsvp_status === 'attending' && ` (${evite.rsvp_count})`}
              </b>
            </p>
          )}
          {rsvpMsg && <p className="mt-2 text-sm text-green-600">{rsvpMsg}</p>}
        </div>

        {/* Download */}
        <a className="btn mt-5 w-full" href={`/api/public/evite/${uuid}/pdf`}>
          Download invitation (PDF)
        </a>

        {/* Verify */}
        <div className="mt-5 border-t border-slate-100 pt-5">
          {evite.can_admit && !evite.attended ? (
            <button className="btn w-full" onClick={admit}>
              Admit guest (staff)
            </button>
          ) : !evite.attended && evite.has_phone ? (
            otpSent ? (
              <div className="space-y-2">
                <input className="input text-center text-lg tracking-widest"
                       placeholder="6-digit code" maxLength={6} value={otp}
                       onChange={(e) => setOtp(e.target.value)} />
                <button className="btn w-full" onClick={verifyOtp} disabled={busy}>
                  Verify
                </button>
              </div>
            ) : (
              <button className="btn-outline w-full" onClick={requestOtp}
                      disabled={busy}>
                Verify with SMS code
              </button>
            )
          ) : null}
          {msg && <p className="mt-2 text-sm text-slate-600">{msg}</p>}
        </div>
      </div>
      <p className="mt-6 text-center text-xs text-slate-400">
        Powered by Angstrom Technologies · events.angstrom-technologies.ug
      </p>
    </Shell>
  )
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-[#f4f8fc] to-white p-4">
      <div className="w-full max-w-md">{children}</div>
    </div>
  )
}
