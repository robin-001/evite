import { useEffect, useRef, useState } from 'react'
import { Html5Qrcode } from 'html5-qrcode'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'

export default function Scan() {
  const nav = useNavigate()
  const [manual, setManual] = useState('')
  const [error, setError] = useState('')
  const [scanning, setScanning] = useState(false)
  const scannerRef = useRef<Html5Qrcode | null>(null)

  function go(text: string) {
    const m = text.match(/evite\/([0-9a-f-]{36})/i) ?? text.match(/^([0-9a-f-]{36})$/i)
    if (m) nav(`/evite/${m[1]}`)
    else setError('Not a valid e-vite QR/link.')
  }

  async function start() {
    setError('')
    setScanning(true)
    try {
      const scanner = new Html5Qrcode('qr-reader')
      scannerRef.current = scanner
      await scanner.start(
        { facingMode: 'environment' },
        { fps: 10, qrbox: 240 },
        (decoded) => {
          stop()
          go(decoded)
        },
        () => {},
      )
    } catch (e: any) {
      setScanning(false)
      setError('Camera unavailable — enter the code manually below.')
    }
  }

  async function stop() {
    setScanning(false)
    try { await scannerRef.current?.stop() } catch { /* already stopped */ }
    scannerRef.current = null
  }

  useEffect(() => () => { scannerRef.current?.stop().catch(() => {}) }, [])

  return (
    <Layout>
      <div className="mx-auto max-w-md">
        <h1 className="mb-4 text-xl font-extrabold text-[#10233f]">
          Scan an invitation
        </h1>
        <div className="card p-5">
          <div id="qr-reader" className="overflow-hidden rounded-lg bg-black" />
          <div className="mt-3 flex gap-2">
            {!scanning
              ? <button className="btn w-full" onClick={start}>Start camera</button>
              : <button className="btn-outline w-full" onClick={stop}>Stop</button>}
          </div>
        </div>
        <div className="card mt-4 p-5">
          <label className="label">Or paste link / UUID</label>
          <div className="flex gap-2">
            <input className="input" value={manual}
                   onChange={(e) => setManual(e.target.value)}
                   placeholder="https://…/evite/xxxx or UUID" />
            <button className="btn" onClick={() => go(manual)}>Open</button>
          </div>
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        </div>
      </div>
    </Layout>
  )
}
