import axios from 'axios'

// All calls go to /api/..., which Vite forwards to FastAPI.
const client = axios.create({ baseURL: '/api', timeout: 90000 })

// Turns any axios error into a readable message for the UI.
export function errorMessage(err) {
  if (err.response?.data?.error) return err.response.data.error
  if (err.code === 'ECONNABORTED') return 'The request timed out. Try again.'
  if (err.response) return `Request failed (HTTP ${err.response.status}).`
  return 'Cannot reach the backend. Is the server running?'
}

export default client