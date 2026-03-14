import api from '../lib/axios'
import toast from 'react-hot-toast'

export const login = async (email, password) => {
  try {
    const response = await api.post('/api/v1/auth/login', { email, password })
    return response.data
  } catch (error) {
    const message = error.response?.data?.detail || 'Login failed'
    toast.error(message)
    throw error
  }
}

export const register = async (userData) => {
  try {
    const response = await api.post('/api/v1/auth/register', userData)
    toast.success('Registration successful!')
    return response.data
  } catch (error) {
    const message = error.response?.data?.detail || 'Registration failed'
    toast.error(message)
    throw error
  }
}

export const logout = async () => {
  try {
    await api.post('/api/v1/auth/logout')
    toast.success('Logged out successfully')
  } catch (error) {
    console.error('Logout error:', error)
  }
}

export const getCurrentUser = async () => {
  try {
    const response = await api.get('/api/v1/auth/me')
    return response.data
  } catch (error) {
    return null
  }
}

export const refreshToken = async () => {
  try {
    const response = await api.post('/api/v1/auth/refresh')
    return response.data
  } catch (error) {
    throw error
  }
}

export const changePassword = async (currentPassword, newPassword) => {
  try {
    const response = await api.post('/api/v1/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword
    })
    toast.success('Password changed successfully')
    return response.data
  } catch (error) {
    toast.error(error.response?.data?.detail || 'Failed to change password')
    throw error
  }
}