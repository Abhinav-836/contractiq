import api from '../lib/axios'

const normalize = (a) => ({
  id: a.id,
  contractId: a.contract_id,
  type: a.type,
  title: a.title,
  message: a.message,
  read: a.read,
  createdAt: a.created_at,
})

export const getAlerts = async (params = {}) => {
  const qs = new URLSearchParams(params).toString()
  const { data } = await api.get(`/api/v1/alerts${qs ? `?${qs}` : ''}`)
  return Array.isArray(data) ? data.map(normalize) : []
}

export const getAlertStats = async () => {
  const { data } = await api.get('/api/v1/alerts/stats')
  return data
}

export const markAlertRead = async (id) => {
  const { data } = await api.patch(`/api/v1/alerts/${id}/read`)
  return data
}

export const markAllAlertsRead = async () => {
  const { data } = await api.post('/api/v1/alerts/mark-all-read')
  return data
}

export const dismissAlert = async (id) => {
  const { data } = await api.delete(`/api/v1/alerts/${id}`)
  return data
}