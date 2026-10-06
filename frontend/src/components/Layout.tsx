import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link to="/" className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#0b5cff] to-[#00a8e8] text-base font-extrabold text-white">
              E
            </span>
            <span className="font-extrabold text-[#10233f]">Event Zone</span>
            <span className="hidden text-[10px] text-slate-400 sm:block">
              by Angstrom Technologies
            </span>
          </Link>
          <div className="flex items-center gap-3">
            <button className="btn-outline" onClick={() => nav('/scan')}>
              Scan
            </button>
            <span className="hidden text-sm text-slate-600 sm:block">
              {user?.name || user?.email}
            </span>
            <button className="btn-outline" onClick={logout}>Log out</button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  )
}
