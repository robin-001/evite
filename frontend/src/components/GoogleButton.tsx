import { useEffect, useRef } from 'react'
import { useAuth } from '../auth'

declare global {
  interface Window { google?: any }
}

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined

export default function GoogleButton({ onError }: { onError?: (m: string) => void }) {
  const { google } = useAuth()
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!CLIENT_ID) return
    const init = () => {
      window.google?.accounts.id.initialize({
        client_id: CLIENT_ID,
        callback: (resp: { credential: string }) =>
          google(resp.credential).catch(() => onError?.('Google sign-in failed')),
      })
      window.google?.accounts.id.renderButton(ref.current, {
        theme: 'outline', size: 'large', width: 320,
      })
    }
    if (window.google) { init(); return }
    const s = document.createElement('script')
    s.src = 'https://accounts.google.com/gsi/client'
    s.async = true
    s.onload = init
    document.head.appendChild(s)
  }, [])

  if (!CLIENT_ID) return null
  return <div ref={ref} className="flex justify-center" />
}
