import { create } from 'zustand'

export const useChatStore = create((set, get) => ({
  sessions: [],
  activeSessionId: null,
  messages: {},
  isTyping: false,

  createSession: (session) => {
    set((state) => ({
      sessions: [session, ...state.sessions],
      activeSessionId: session.id,
      messages: { ...state.messages, [session.id]: [] },
    }))
    return session
  },

  setActiveSession: (id) => set({ activeSessionId: id }),

  addMessage: (sessionId, message) =>
    set((state) => ({
      messages: {
        ...state.messages,
        [sessionId]: [...(state.messages[sessionId] || []), message],
      },
    })),

  updateLastMessage: (sessionId, updates) =>
    set((state) => {
      const msgs = state.messages[sessionId] || []
      const updated = [...msgs]
      if (updated.length > 0) {
        updated[updated.length - 1] = { ...updated[updated.length - 1], ...updates }
      }
      return { messages: { ...state.messages, [sessionId]: updated } }
    }),

  setIsTyping: (val) => set({ isTyping: val }),

  getActiveMessages: () => {
    const { activeSessionId, messages } = get()
    return activeSessionId ? messages[activeSessionId] || [] : []
  },
}))
