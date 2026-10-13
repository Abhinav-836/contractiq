import api from '../lib/axios'

// Normalize backend snake_case → frontend camelCase
const normalize = (o) => ({
  id: o.id,
  contractId: o.contract_id,
  title: o.title,
  description: o.description,
  status: o.status,
  priority: o.priority,
  dueDate: o.due_date,
  assignedTo: o.assigned_to,
  createdAt: o.created_at,
})

export const getObligations = async (params = {}) => {
  const qs = new URLSearchParams(params).toString()
  const { data } = await api.get(`/api/v1/obligations${qs ? `?${qs}` : ''}`)
  return Array.isArray(data) ? data.map(normalize) : []
}

export const getObligation = async (id) => {
  const { data } = await api.get(`/api/v1/obligations/${id}`)
  return normalize(data)
}

export const completeObligation = async (id) => {
  const { data } = await api.patch(`/api/v1/obligations/${id}/complete`)
  return data
}

export const updateObligation = async (id, patch) => {
  const { data } = await api.patch(`/api/v1/obligations/${id}`, patch)
  return data
}

export const deleteObligation = async (id) => {
  const { data } = await api.delete(`/api/v1/obligations/${id}`)
  return data
}

export const getObligationStats = async () => {
  const { data } = await api.get('/api/v1/obligations/stats')
  return data
}