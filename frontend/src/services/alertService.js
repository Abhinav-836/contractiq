import api from '../lib/axios'

export const getAlerts = async (params = {}) => {
  const queryParams = new URLSearchParams(params).toString()
  const response = await api.get(`/api/v1/alerts${queryParams ? `?${queryParams}` : ''}`)
  return response.data
}

export const getAlertStats = async () => {
  const response = await api.get('/api/v1/alerts/stats')
  return response.data
}

export const markAlertRead = async (id) => {
  const response = await api.patch(`/api/v1/alerts/${id}/read`)
  return response.data
}

export const markAllAlertsRead = async () => {
  const response = await api.post('/api/v1/alerts/mark-all-read')
  return response.data
}

export const dismissAlert = async (id) => {
  const response = await api.delete(`/api/v1/alerts/${id}`)
  return response.data
}