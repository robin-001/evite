import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import GoogleButton from '../components/GoogleButton'

export default function Register() {
  const { register } = useAuth()
  const nav = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true); setError('')
    try { await register(form.email, form.password, form.name); nav('/') }
    catch (err: any) {
      setError(err.response?.data?.email?.[0] ?? 'Registration failed.')
    } finally { setBusy(false) }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="card w-full max-w-sm p-8">
        <h1 className="mb-6 text-center text-xl font-extrabold text-[#10233f]">
          Create your organiser account
        </h1>
        <GoogleButton onError={setError} />
        <div className="my-4 flex items-center gap-3 text-xs text-slate-400">
          <div className="h-px flex-1 bg-slate-200" /> or <div className="h-px flex-1 bg-slate-200" />
        </div>
        <form onSubmit={submit} className="space-y-3">
          <input className="input" placeholder="Full name"
                 value={form.name}
                 onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input className="input" type="email" placeholder="Email" required
                 value={form.email}
                 onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <input className="input" type="password" placeholder="Password (8+ chars)"
                 required minLength={8} value={form.password}
                 onChange={(e) => setForm({ ...form, password: e.target.value })} />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button className="btn w-full" disabled={busy}>
            {busy ? 'Creating…' : 'Create account'}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500">
          Have an account? <Link to="/login" className="font-semibold text-[#0b5cff]">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
