import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export function setTokens(access: string, refresh: string) {
  localStorage.setItem('access', access)
  localStorage.setItem('refresh', refresh)
}
export function clearTokens() {
  localStorage.removeItem('access')
  localStorage.removeItem('refresh')
}
export function getAccess() { return localStorage.getItem('access') }
export function getRefresh() { return localStorage.getItem('refresh') }

api.interceptors.request.use((config) => {
  const token = getAccess()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshing: Promise<string> | null = null

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const orig = error.config
    if (error.response?.status !== 401 || orig._retried || !getRefresh()) {
      return Promise.reject(error)
    }
    orig._retried = true
    try {
      refreshing = refreshing ?? axios
        .post('/api/auth/refresh', { refresh: getRefresh() })
        .then((r) => {
          setTokens(r.data.access, getRefresh()!)
          return r.data.access as string
        })
        .finally(() => { refreshing = null })
      orig.headers.Authorization = `Bearer ${await refreshing}`
      return api(orig)
    } catch {
      clearTokens()
      window.location.href = '/login'
      return Promise.reject(error)
    }
  },
)

export default api
