import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

if (import.meta.env.DEV) {
  console.log('🔧 API Base URL:', baseURL)
}

export const api = axios.create({
  baseURL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor — attach JWT
api.interceptors.request.use(
  (config) => {
    const token = sessionStorage.getItem('ciq_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    if (import.meta.env.DEV) {
      console.log(`📤 ${config.method?.toUpperCase()} ${config.url}`)
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor — handle 401 globally
api.interceptors.response.use(
  (res) => {
    if (import.meta.env.DEV) {
      console.log(`📥 ${res.config.method?.toUpperCase()} ${res.config.url} → ${res.status}`)
    }
    return res
  },
  (err) => {
    const status = err.response?.status
    const url = err.config?.url || ''

    if (import.meta.env.DEV) {
      const msg = err.response?.data?.detail || err.message
      console.error(`❌ ${err.config?.method?.toUpperCase()} ${url} → ${status}`, msg)
    }

    // Auto-logout on 401 for non-auth endpoints
    if (status === 401 && !url.includes('/auth/login') && !url.includes('/auth/register')) {
      sessionStorage.removeItem('ciq_token')
      sessionStorage.removeItem('auth-storage')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }

    return Promise.reject(err)
  }
)

export default api