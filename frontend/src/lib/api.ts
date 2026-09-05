import axios from 'axios'

// WHY withCredentials: true - the backend authenticates via an httpOnly
// cookie, not a bearer token in a header. Without this flag, the browser
// won't send that cookie on cross-origin requests (the frontend dev server
// on :5173 and the API on :8000 are different origins), so every request
// would look unauthenticated even right after a successful login.
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,
})

// Attach Bearer token from localStorage as fallback when cross-site cookies are blocked
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('recruitflow_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export interface ApiErrorShape {
  detail?: string | Array<{ loc?: string[]; msg?: string; type?: string }> | Record<string, unknown>
}

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') {
      return detail
    }
    if (Array.isArray(detail) && detail.length > 0) {
      return detail
        .map((item) => {
          if (typeof item === 'object' && item !== null && 'msg' in item) {
            const loc = Array.isArray(item.loc)
              ? item.loc.filter((part: string) => part !== 'body').join('.')
              : ''
            const msg = String(item.msg).replace(/^Value error, /i, '')
            return loc ? `${loc}: ${msg}` : msg
          }
          return typeof item === 'string' ? item : JSON.stringify(item)
        })
        .join(', ')
    }
    if (detail && typeof detail === 'object') {
      return JSON.stringify(detail)
    }
    return error.message || 'Something went wrong'
  }
  return error instanceof Error ? error.message : 'Something went wrong'
}
