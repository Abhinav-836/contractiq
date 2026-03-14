import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '../lib/axios'
import toast from 'react-hot-toast'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email, password) => {
        set({ isLoading: true })
        try {
          const response = await api.post('/api/v1/auth/login', { email, password })
          const { access_token, user } = response.data
          
          // Store token
          sessionStorage.setItem('ciq_token', access_token)
          
          set({ 
            user, 
            token: access_token, 
            isAuthenticated: true,
            isLoading: false 
          })
          
          toast.success(`Welcome back, ${user.name}!`)
          return { success: true }
        } catch (error) {
          set({ isLoading: false })
          const message = error.response?.data?.detail || 'Login failed'
          toast.error(message)
          return { success: false, error: message }
        }
      },

      register: async (userData) => {
        set({ isLoading: true })
        try {
          const response = await api.post('/api/v1/auth/register', userData)
          const { access_token, user } = response.data
          
          sessionStorage.setItem('ciq_token', access_token)
          
          set({ 
            user, 
            token: access_token, 
            isAuthenticated: true,
            isLoading: false 
          })
          
          toast.success('Account created successfully!')
          return { success: true }
        } catch (error) {
          set({ isLoading: false })
          const message = error.response?.data?.detail || 'Registration failed'
          toast.error(message)
          return { success: false, error: message }
        }
      },

      logout: () => {
        sessionStorage.removeItem('ciq_token')
        set({ user: null, token: null, isAuthenticated: false })
        toast.success('Logged out successfully')
      },

      updateUser: (userData) => {
        set({ user: { ...get().user, ...userData } })
      },
    }),
    {
      name: 'auth-storage',
      getStorage: () => sessionStorage,
    }
  )
)