import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import GoogleButton from '../components/GoogleButton'

export default function Login() {
  const { login } = useAuth()
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true); setError('')
    try { await login(email, password); nav('/') }
    catch { setError('Invalid email or password.') }
    finally { setBusy(false) }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="card w-full max-w-sm p-8">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-[#0b5cff] to-[#00a8e8] text-xl font-extrabold text-white">E</div>
          <h1 className="text-xl font-extrabold text-[#10233f]">Event Zone</h1>
          <p className="text-xs text-slate-500">by Angstrom Technologies</p>
        </div>
        <GoogleButton onError={setError} />
        <div className="my-4 flex items-center gap-3 text-xs text-slate-400">
          <div className="h-px flex-1 bg-slate-200" /> or <div className="h-px flex-1 bg-slate-200" />
        </div>
        <form onSubmit={submit} className="space-y-3">
          <input className="input" type="email" placeholder="Email" required
                 value={email} onChange={(e) => setEmail(e.target.value)} />
          <input className="input" type="password" placeholder="Password" required
                 value={password} onChange={(e) => setPassword(e.target.value)} />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button className="btn w-full" disabled={busy}>
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500">
          No account? <Link to="/register" className="font-semibold text-[#0b5cff]">Register</Link>
        </p>
      </div>
    </div>
  )
}
