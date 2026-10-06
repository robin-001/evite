import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import Layout from '../components/Layout'
import type { Event } from '../types'

export default function Dashboard() {
  const [events, setEvents] = useState<Event[]>([])
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({ name: '', date_text: '', venue: '', dress_code: '' })

  const load = () => api.get('/events/').then((r) => setEvents(r.data))
  useEffect(() => { load() }, [])

  async function create(e: React.FormEvent) {
    e.preventDefault()
    await api.post('/events/', form)
    setCreating(false)
    setForm({ name: '', date_text: '', venue: '', dress_code: '' })
    load()
  }

  return (
    <Layout>
      <div className="mb-5 flex items-center justify-between">
        <h1 className="text-2xl font-extrabold text-[#10233f]">My Events</h1>
        <button className="btn" onClick={() => setCreating(true)}>+ New event</button>
      </div>

      {creating && (
        <form onSubmit={create} className="card mb-5 grid gap-3 p-5 sm:grid-cols-2">
          <input className="input" placeholder="Event name" required
                 value={form.name}
                 onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input className="input" placeholder="Date (e.g. Friday 30th October 2026)"
                 value={form.date_text}
                 onChange={(e) => setForm({ ...form, date_text: e.target.value })} />
          <input className="input" placeholder="Venue"
                 value={form.venue}
                 onChange={(e) => setForm({ ...form, venue: e.target.value })} />
          <input className="input" placeholder="Dress code"
                 value={form.dress_code}
                 onChange={(e) => setForm({ ...form, dress_code: e.target.value })} />
          <div className="flex gap-2 sm:col-span-2">
            <button className="btn" type="submit">Create</button>
            <button className="btn-outline" type="button"
                    onClick={() => setCreating(false)}>Cancel</button>
          </div>
        </form>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {events.map((ev) => (
          <Link key={ev.id} to={`/events/${ev.id}`}
                className="card p-5 transition hover:shadow-md">
            <div className="mb-1 text-base font-bold text-[#10233f]">{ev.name}</div>
            <div className="text-sm text-slate-500">{ev.date_text}</div>
            <div className="text-sm text-slate-500">{ev.venue}</div>
            <div className="mt-3 flex items-center justify-between text-xs">
              <span className="rounded-full bg-blue-50 px-2 py-0.5 font-semibold text-[#0b5cff]">
                {ev.my_role}
              </span>
              <span className="text-slate-400">{ev.guest_count ?? 0} guests</span>
            </div>
          </Link>
        ))}
        {!events.length && (
          <p className="text-sm text-slate-500">
            No events yet — create your first one.
          </p>
        )}
      </div>
    </Layout>
  )
}
