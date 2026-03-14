import axios from 'axios'

// Get base URL from environment variable, fallback to localhost for development
const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

console.log('🔧 API Base URL:', baseURL)

export const api = axios.create({
  baseURL: baseURL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token if present
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('ciq_token')
  if (token && token !== 'no-auth-token') {
    config.headers.Authorization = `Bearer ${token}`
  }
  
  // Log requests in development
  if (import.meta.env.DEV) {
    console.log(`📤 ${config.method?.toUpperCase()} ${config.url}`, config.data || '')
  }
  
  return config
})

api.interceptors.response.use(
  (res) => {
    // Log responses in development
    if (import.meta.env.DEV) {
      console.log(`📥 ${res.config.method?.toUpperCase()} ${res.config.url} →`, res.status)
    }
    return res
  },
  (err) => {
    const msg = err.response?.data?.detail || err.message
    console.error(`❌ API ${err.config?.method?.toUpperCase()} ${err.config?.url} →`, msg)
    
    // Log more details for debugging
    if (err.response) {
      console.error('Status:', err.response.status)
      console.error('Data:', err.response.data)
    } else if (err.request) {
      console.error('No response received from server')
      console.error('Check if backend is running at:', baseURL)
    } else {
      console.error('Request error:', err.message)
    }
    
    return Promise.reject(err)
  }
)

export default api