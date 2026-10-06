import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import EventWorkspace from './pages/EventWorkspace'
import Scan from './pages/Scan'
import EvitePublic from './pages/EvitePublic'

function Guard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="p-10 text-center text-slate-500">Loading…</div>
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/evite/:uuid" element={<EvitePublic />} />
          <Route path="/" element={<Guard><Dashboard /></Guard>} />
          <Route path="/events/:id" element={<Guard><EventWorkspace /></Guard>} />
          <Route path="/scan" element={<Guard><Scan /></Guard>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
