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

export interface ApiErrorShape {
  detail?: string
}

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ApiErrorShape>(error)) {
    return error.response?.data?.detail ?? error.message
  }
  return 'Something went wrong'
}
