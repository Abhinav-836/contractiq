import api from '../lib/axios'

// Re-export all services
export * from './authService'
export * from './contractService'
export * from './analysisService'
export * from './obligationService'
export * from './alertService'
export * from './chatService'

// System status
export const getSystemStatus = async () => {
  try {
    const response = await api.get('/api/v1/health')
    return response.data
  } catch (error) {
    console.error('Failed to get system status:', error)
    return { status: 'unhealthy' }
  }
}

export const getLLMStatus = async () => {
  try {
    const response = await api.get('/api/v1/llm/status')
    return response.data
  } catch (error) {
    console.error('Failed to get LLM status:', error)
    return { provider: 'unknown', available_providers: {} }
  }
}

export const getAvailableModels = async () => {
  try {
    const response = await api.get('/api/v1/llm/models')
    return response.data
  } catch (error) {
    console.error('Failed to fetch models:', error)
    return { models: [], active: 'unknown' }
  }
}

// Dashboard stats
export const getDashboardStats = async () => {
  try {
    const [contracts, alerts, obligations] = await Promise.all([
      api.get('/api/v1/contracts/stats'),
      api.get('/api/v1/alerts/stats'),
      api.get('/api/v1/obligations/stats')
    ])
    
    return {
      contracts: contracts.data,
      alerts: alerts.data,
      obligations: obligations.data
    }
  } catch (error) {
    console.error('Failed to fetch dashboard stats:', error)
    return {
      contracts: { total: 0, highRisk: 0, mediumRisk: 0, lowRisk: 0 },
      alerts: { total: 0, unread: 0 },
      obligations: { total: 0, overdue: 0, pending: 0 }
    }
  }
}