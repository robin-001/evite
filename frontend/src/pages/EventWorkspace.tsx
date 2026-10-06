import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import Cropper from 'react-easy-crop'
import api from '../api'
import Layout from '../components/Layout'
import type { Event, Guest, Member, SmsLog, GenStatus } from '../types'

type Tab = 'guests' | 'card' | 'send' | 'team'

export default function EventWorkspace() {
  const { id } = useParams()
  const [event, setEvent] = useState<Event | null>(null)
  const [tab, setTab] = useState<Tab>('guests')

  const load = useCallback(
    () => api.get(`/events/${id}`).then((r) => setEvent(r.data)),
    [id],
  )
  useEffect(() => { load() }, [load])

  if (!event) return <Layout><div className="p-10 text-center">Loading…</div></Layout>
  const canEdit = event.my_role === 'owner' || event.my_role === 'manager'

  const tabs: { key: Tab; label: string }[] = [
    { key: 'guests', label: 'Guests' },
    { key: 'card', label: 'Card' },
    { key: 'send', label: 'Send' },
    { key: 'team', label: 'Team' },
  ]

  return (
    <Layout>
      <div className="mb-4">
        <h1 className="text-xl font-extrabold text-[#10233f]">{event.name}</h1>
        <p className="text-sm text-slate-500">
          {event.date_text} · {event.venue} · role: {event.my_role}
        </p>
      </div>

      <div className="mb-5 flex gap-1 border-b border-slate-200">
        {tabs.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
                  className={`px-4 py-2 text-sm font-semibold border-b-2 -mb-px transition
                    ${tab === t.key
                      ? 'border-[#0b5cff] text-[#0b5cff]'
                      : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'guests' && <GuestsTab event={event} canEdit={canEdit} />}
      {tab === 'card' && <CardTab event={event} canEdit={canEdit} onSaved={load} />}
      {tab === 'send' && <SendTab event={event} canEdit={canEdit} />}
      {tab === 'team' && <TeamTab event={event} />}
    </Layout>
  )
}

/* ---------------- Guests ---------------- */

function GuestsTab({ event, canEdit }: { event: Event; canEdit: boolean }) {
  const [guests, setGuests] = useState<Guest[]>([])
  const [importResult, setImportResult] = useState('')
  const [busy, setBusy] = useState(false)

  const load = useCallback(
    () => api.get(`/events/${event.id}/guests`).then((r) => setGuests(r.data)),
    [event.id],
  )
  useEffect(() => { load() }, [load])

  async function upload(file: File) {
    setBusy(true)
    const fd = new FormData()
    fd.append('file', file)
    const r = await api.post(`/events/${event.id}/guests/import`, fd)
    setImportResult(`Imported ${r.data.created} guests, skipped ${r.data.skipped}`)
    setBusy(false)
    load()
  }

  async function remove(gid: number) {
    await api.delete(`/events/guests/${gid}`)
    load()
  }

  return (
    <div>
      {canEdit && (
        <div className="card mb-4 flex flex-wrap items-center gap-3 p-4">
          <label className="btn-outline cursor-pointer">
            {busy ? 'Importing…' : 'Import CSV (title,name,phone,admits)'}
            <input type="file" accept=".csv" className="hidden" disabled={busy}
                   onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} />
          </label>
          {importResult && <span className="text-sm text-green-600">{importResult}</span>}
        </div>
      )}
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-400">
              <th className="p-3">Guest</th><th className="p-3">Phone(s)</th>
              <th className="p-3">Admits</th><th className="p-3">RSVP</th>
              <th className="p-3">Attended</th><th className="p-3" />
            </tr>
          </thead>
          <tbody>
            {guests.map((g) => (
              <tr key={g.id} className="border-b border-slate-100 last:border-0">
                <td className="p-3 font-semibold">
                  {g.title} {g.name}
                </td>
                <td className="p-3 text-slate-600">
                  {g.phones?.join(' / ') || '—'}
                </td>
                <td className="p-3">{g.admits}</td>
                <td className="p-3">
                  <RsvpBadge status={g.rsvp_status} count={g.rsvp_count} />
                </td>
                <td className="p-3">
                  {g.attended
                    ? <span className="font-semibold text-green-600">Admitted</span>
                    : <span className="text-slate-400">—</span>}
                </td>
                <td className="p-3 text-right">
                  {canEdit && (
                    <button className="text-xs text-red-500 hover:underline"
                            onClick={() => remove(g.id)}>Remove</button>
                  )}
                </td>
              </tr>
            ))}
            {!guests.length && (
              <tr><td colSpan={6} className="p-6 text-center text-slate-400">
                No guests yet — import a CSV.
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function RsvpBadge({ status, count }: { status: string; count: number }) {
  const styles: Record<string, string> = {
    attending: 'bg-green-50 text-green-700',
    declined: 'bg-red-50 text-red-600',
    pending: 'bg-slate-100 text-slate-500',
  }
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${styles[status]}`}>
      {status === 'attending' ? `Attending (${count})` : status}
    </span>
  )
}

/* ---------------- Card ---------------- */

function CardTab({ event, canEdit, onSaved }:
  { event: Event; canEdit: boolean; onSaved: () => void }) {
  const [form, setForm] = useState({
    card_bg_color: event.card_bg_color,
    card_text_color: event.card_text_color,
    card_accent_color: event.card_accent_color,
    message_template: event.message_template,
    rsvp_contacts: (event.rsvp_contacts || []).join('\n'),
    date_text: event.date_text,
    venue: event.venue,
    dress_code: event.dress_code,
    name: event.name,
  })
  const [previewHtml, setPreviewHtml] = useState('')
  const [guests, setGuests] = useState<Guest[]>([])
  const [guestId, setGuestId] = useState<number | null>(null)
  const [cropSrc, setCropSrc] = useState<string | null>(null)
  const [crop, setCrop] = useState({ x: 0, y: 0 })
  const [zoom, setZoom] = useState(1)
  const [saved, setSaved] = useState('')

  useEffect(() => {
    api.get(`/events/${event.id}/guests`).then((r) => {
      setGuests(r.data)
      if (r.data.length) setGuestId(r.data[0].id)
    })
  }, [event.id])

  useEffect(() => {
    if (!guestId) return
    api.get(`/events/${event.id}/guests/${guestId}/preview`)
      .then((r) => setPreviewHtml(r.data))
  }, [guestId, event.id, event.artwork, form.card_bg_color,
      form.card_text_color])

  async function save() {
    await api.patch(`/events/${event.id}/card`, {
      ...form,
      rsvp_contacts: form.rsvp_contacts.split('\n').map((s) => s.trim()).filter(Boolean),
    })
    setSaved('Saved'); setTimeout(() => setSaved(''), 2000)
    onSaved()
  }

  function pickArtwork(file: File) {
    const reader = new FileReader()
    reader.onload = () => setCropSrc(reader.result as string)
    reader.readAsDataURL(file)
  }

  async function confirmCrop() {
    const fd = new FormData()
    const input = document.querySelector<HTMLInputElement>('#artwork-file')
    if (!input?.files?.[0]) return
    fd.append('file', input.files[0])
    await api.post(`/events/${event.id}/artwork`, fd)
    await api.patch(`/events/${event.id}/card`,
                     { artwork_crop: { x: crop.x, y: crop.y, zoom } })
    setCropSrc(null)
    onSaved()
  }

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <div className="space-y-4">
        <div className="card p-5">
          <label className="label">Artwork / background image</label>
          <input id="artwork-file" type="file" accept="image/*"
                 className="input" disabled={!canEdit}
                 onChange={(e) => e.target.files?.[0] && pickArtwork(e.target.files[0])} />
        </div>

        {cropSrc && (
          <div className="card p-5">
            <label className="label">Crop artwork</label>
            <div className="relative h-64 w-full overflow-hidden rounded-lg bg-black">
              <Cropper image={cropSrc} crop={crop} zoom={zoom}
                       aspect={850 / 500} onCropChange={setCrop}
                       onZoomChange={setZoom} />
            </div>
            <div className="mt-3 flex gap-2">
              <button className="btn" onClick={confirmCrop}>Save artwork</button>
              <button className="btn-outline" onClick={() => setCropSrc(null)}>Cancel</button>
            </div>
          </div>
        )}

        <div className="card space-y-3 p-5">
          <label className="label">Theme</label>
          {([['card_bg_color', 'Background'], ['card_text_color', 'Text'],
             ['card_accent_color', 'Accent / rules']] as const).map(([k, l]) => (
            <div key={k} className="flex items-center justify-between">
              <span className="text-sm">{l}</span>
              <input type="color" disabled={!canEdit}
                     value={(form as any)[k]}
                     onChange={(e) => setForm({ ...form, [k]: e.target.value })}
                     className="h-8 w-14 cursor-pointer rounded border" />
            </div>
          ))}
        </div>

        <div className="card space-y-3 p-5">
          <label className="label">Event details (shown on card)</label>
          <input className="input" placeholder="Event name" value={form.name} disabled={!canEdit}
                 onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input className="input" placeholder="Date text" value={form.date_text} disabled={!canEdit}
                 onChange={(e) => setForm({ ...form, date_text: e.target.value })} />
          <input className="input" placeholder="Venue" value={form.venue} disabled={!canEdit}
                 onChange={(e) => setForm({ ...form, venue: e.target.value })} />
          <input className="input" placeholder="Dress code" value={form.dress_code} disabled={!canEdit}
                 onChange={(e) => setForm({ ...form, dress_code: e.target.value })} />
          <textarea className="input" rows={2} disabled={!canEdit}
                    placeholder="RSVP contacts, one per line"
                    value={form.rsvp_contacts}
                    onChange={(e) => setForm({ ...form, rsvp_contacts: e.target.value })} />
        </div>

        <div className="card space-y-2 p-5">
          <label className="label">Invite SMS template</label>
          <textarea className="input" rows={3} disabled={!canEdit}
                    value={form.message_template}
                    onChange={(e) => setForm({ ...form, message_template: e.target.value })} />
          <p className="text-xs text-slate-400">
            Variables: {'{title}'} {'{name}'} {'{first_name}'} {'{event}'} {'{link}'}
          </p>
          <div className="flex items-center gap-2 pt-1">
            <button className="btn" onClick={save} disabled={!canEdit}>Save card</button>
            {saved && <span className="text-sm text-green-600">{saved}</span>}
          </div>
        </div>
      </div>

      <div className="card p-4">
        <label className="label">Live preview</label>
        <select className="input mb-3" value={guestId ?? ''}
                onChange={(e) => setGuestId(Number(e.target.value))}>
          {guests.map((g) => (
            <option key={g.id} value={g.id}>{g.title} {g.name}</option>
          ))}
        </select>
        {previewHtml
          ? <iframe srcDoc={previewHtml} className="h-[700px] w-full rounded-lg border" />
          : <p className="text-sm text-slate-400">Import guests to preview the card.</p>}
      </div>
    </div>
  )
}

/* ---------------- Send ---------------- */

function SendTab({ event, canEdit }: { event: Event; canEdit: boolean }) {
  const [status, setStatus] = useState<GenStatus | null>(null)
  const [logs, setLogs] = useState<SmsLog[]>([])
  const [sendResult, setSendResult] = useState('')
  const poll = useRef<ReturnType<typeof setInterval> | undefined>(undefined)

  const loadLogs = useCallback(
    () => api.get(`/events/${event.id}/sms-log`).then((r) => setLogs(r.data)),
    [event.id],
  )
  useEffect(() => { loadLogs() }, [loadLogs])

  async function generate() {
    const r = await api.post(`/events/${event.id}/generate`)
    const jobId = r.data.job_id
    poll.current = setInterval(async () => {
      const s = await api.get(`/events/${event.id}/generate/status`)
      setStatus(s.data)
      if (s.data.status === 'done' || s.data.status === 'failed') {
        clearInterval(poll.current)
      }
      void jobId
    }, 1000)
  }
  useEffect(() => () => clearInterval(poll.current), [])

  async function send() {
    if (!confirm('Send invite SMS to all guests?')) return
    const r = await api.post(`/events/${event.id}/send`)
    setSendResult(
      r.data.live
        ? `Sent ${r.data.sent}, failed ${r.data.failed}, skipped ${r.data.guests_without_phone}`
        : `DRY RUN — ${r.data.dry_run} messages logged, none sent`)
    loadLogs()
  }

  return (
    <div className="space-y-4">
      {canEdit && (
        <div className="card flex flex-wrap items-center gap-3 p-4">
          <button className="btn" onClick={generate}>Generate cards</button>
          <button className="btn" onClick={send}>Send invites</button>
          {status && status.status !== 'none' && (
            <span className="text-sm text-slate-600">
              PDFs: {status.done}/{status.total}
              {status.status === 'failed' && ` — ${status.error}`}
            </span>
          )}
          {sendResult && <span className="text-sm text-green-600">{sendResult}</span>}
        </div>
      )}
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-400">
              <th className="p-3">Guest</th><th className="p-3">Phone</th>
              <th className="p-3">Kind</th><th className="p-3">Status</th>
              <th className="p-3">Sent at</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((l) => (
              <tr key={l.id} className="border-b border-slate-100 last:border-0">
                <td className="p-3 font-semibold">{l.guest_name}</td>
                <td className="p-3">{l.phone}</td>
                <td className="p-3">{l.kind}</td>
                <td className="p-3">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                    l.status === 'sent' ? 'bg-green-50 text-green-700'
                    : l.status === 'failed' ? 'bg-red-50 text-red-600'
                    : 'bg-slate-100 text-slate-500'}`}>{l.status}</span>
                </td>
                <td className="p-3 text-slate-500">
                  {new Date(l.sent_at).toLocaleString()}
                </td>
              </tr>
            ))}
            {!logs.length && (
              <tr><td colSpan={5} className="p-6 text-center text-slate-400">
                No SMS activity yet.
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

/* ---------------- Team ---------------- */

function TeamTab({ event }: { event: Event }) {
  const [members, setMembers] = useState<Member[]>([])
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<'manager' | 'scanner'>('scanner')
  const isOwner = event.my_role === 'owner'

  const load = useCallback(
    () => api.get(`/events/${event.id}/members`).then((r) => setMembers(r.data)),
    [event.id],
  )
  useEffect(() => { if (isOwner) load() }, [load, isOwner])

  async function invite(e: React.FormEvent) {
    e.preventDefault()
    await api.post(`/events/${event.id}/members`, { email, role })
    setEmail('')
    load()
  }

  if (!isOwner) {
    return <p className="text-sm text-slate-500">Only the event owner manages the team.</p>
  }

  return (
    <div>
      <form onSubmit={invite} className="card mb-4 flex flex-wrap items-end gap-3 p-4">
        <div className="min-w-60 flex-1">
          <label className="label">Invite by email</label>
          <input className="input" type="email" required value={email}
                 onChange={(e) => setEmail(e.target.value)}
                 placeholder="helper@example.com" />
        </div>
        <div>
          <label className="label">Role</label>
          <select className="input" value={role}
                  onChange={(e) => setRole(e.target.value as 'manager' | 'scanner')}>
            <option value="scanner">Scanner (door)</option>
            <option value="manager">Manager</option>
          </select>
        </div>
        <button className="btn">Invite</button>
      </form>

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-400">
              <th className="p-3">Email</th><th className="p-3">Name</th>
              <th className="p-3">Role</th><th className="p-3">Status</th>
              <th className="p-3" />
            </tr>
          </thead>
          <tbody>
            {members.map((m) => (
              <tr key={m.id} className="border-b border-slate-100 last:border-0">
                <td className="p-3">{m.email}</td>
                <td className="p-3">{m.name || '—'}</td>
                <td className="p-3">{m.role}</td>
                <td className="p-3">
                  {m.invited_email
                    ? <span className="text-amber-600">Pending signup</span>
                    : <span className="text-green-600">Active</span>}
                </td>
                <td className="p-3 text-right">
                  <button className="text-xs text-red-500 hover:underline"
                          onClick={() => api.delete(`/events/members/${m.id}`).then(load)}>
                    Remove
                  </button>
                </td>
              </tr>
            ))}
            {!members.length && (
              <tr><td colSpan={5} className="p-6 text-center text-slate-400">
                No team members yet.
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
