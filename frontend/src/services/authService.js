import api from '../lib/axios'

export const login = async (email, password) => {
  const { data } = await api.post('/api/v1/auth/login', { email, password })
  return data
}

export const register = async (userData) => {
  const { data } = await api.post('/api/v1/auth/register', userData)
  return data
}

export const getCurrentUser = async () => {
  try {
    const { data } = await api.get('/api/v1/auth/me')
    return data
  } catch {
    return null
  }
}