import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { api } from '../lib/axios'
import toast from 'react-hot-toast'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      _hasHydrated: false,

      setHasHydrated: (v) => set({ _hasHydrated: v }),

      login: async (email, password) => {
        set({ isLoading: true })
        try {
          const { data } = await api.post('/api/v1/auth/login', { email, password })
          const { access_token, user } = data
          sessionStorage.setItem('ciq_token', access_token)
          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
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
          const { data } = await api.post('/api/v1/auth/register', userData)
          const { access_token, user } = data
          sessionStorage.setItem('ciq_token', access_token)
          set({
            user,
            token: access_token,
            isAuthenticated: true,
            isLoading: false,
          })
          toast.success('Account created!')
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
        toast.success('Logged out')
      },

      updateUser: (userData) => set({ user: { ...get().user, ...userData } }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true)
      },
    }
  )
)