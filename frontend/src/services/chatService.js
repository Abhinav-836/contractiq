import api from '../lib/axios'

export const getChatSessions = async () => {
  try {
    const response = await api.get('/api/v1/chat/sessions')
    return response.data
  } catch (error) {
    console.error('Failed to fetch chat sessions:', error)
    return []
  }
}

export const createChatSession = async (title) => {
  try {
    const response = await api.post('/api/v1/chat/sessions', { title })
    return response.data
  } catch (error) {
    console.error('Failed to create chat session:', error)
    throw error
  }
}

export const getChatMessages = async (sessionId) => {
  try {
    const response = await api.get(`/api/v1/chat/sessions/${sessionId}/messages`)
    return response.data
  } catch (error) {
    console.error('Failed to fetch messages:', error)
    return []
  }
}

export const sendMessage = async (sessionId, content) => {
  try {
    const response = await api.post(`/api/v1/chat/sessions/${sessionId}/messages`, {
      content
    })
    return response.data
  } catch (error) {
    console.error('Failed to send message:', error)
    throw error
  }
}

export const deleteChatSession = async (sessionId) => {
  try {
    await api.delete(`/api/v1/chat/sessions/${sessionId}`)
  } catch (error) {
    console.error('Failed to delete chat session:', error)
    throw error
  }
}

export const getChatContext = async (contractId) => {
  try {
    const response = await api.get(`/api/v1/chat/context/${contractId}`)
    return response.data
  } catch (error) {
    console.error('Failed to fetch chat context:', error)
    return null
  }
}