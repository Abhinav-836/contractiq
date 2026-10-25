import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { api } from '../lib/axios'
import toast from 'react-hot-toast'
import { queryClient } from '../lib/queryClient'

// FastAPI 422 errors return `detail` as an array of objects — passing that to
// toast() renders "[object Object]". Also covers Render cold-start timeouts.
const errorMessage = (error, fallback) => {
  const detail = error.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg.replace(/^Value error, /, '')
  if (!error.response) return 'Server is waking up or unreachable — please try again in a few seconds'
  return fallback
}

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
          // Drop any cached data from a previous account in this tab
          queryClient.clear()
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
          const message = errorMessage(error, 'Login failed')
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
          queryClient.clear()
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
          const message = errorMessage(error, 'Registration failed')
          toast.error(message)
          return { success: false, error: message }
        }
      },

      logout: () => {
        sessionStorage.removeItem('ciq_token')
        // Without this, the next user to sign in on this tab briefly sees the
        // previous user's contracts/alerts from the 5-minute query cache.
        queryClient.clear()
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