import { createContext, useContext, useEffect, useState } from 'react'
import api, { setTokens, clearTokens } from './api'
import type { User } from './types'

interface AuthCtx {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name: string) => Promise<void>
  google: (credential: string) => Promise<void>
  logout: () => void
}

const Ctx = createContext<AuthCtx>(null as unknown as AuthCtx)
export const useAuth = () => useContext(Ctx)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!localStorage.getItem('access')) { setLoading(false); return }
    api.get('/auth/me')
      .then((r) => setUser(r.data))
      .catch(() => clearTokens())
      .finally(() => setLoading(false))
  }, [])

  async function finish(resp: { access: string; refresh: string; user: User }) {
    setTokens(resp.access, resp.refresh)
    setUser(resp.user)
  }
  const login = (email: string, password: string) =>
    api.post('/auth/login', { email, password }).then((r) => finish(r.data))
  const register = (email: string, password: string, name: string) =>
    api.post('/auth/register', { email, password, name }).then((r) => finish(r.data))
  const google = (credential: string) =>
    api.post('/auth/google', { credential }).then((r) => finish(r.data))
  const logout = () => { clearTokens(); setUser(null) }

  return (
    <Ctx.Provider value={{ user, loading, login, register, google, logout }}>
      {children}
    </Ctx.Provider>
  )
}
