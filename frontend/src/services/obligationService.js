import api from '../lib/axios'

export const getObligations = async (params = {}) => {
  const queryParams = new URLSearchParams(params).toString()
  const response = await api.get(`/api/v1/obligations${queryParams ? `?${queryParams}` : ''}`)
  return response.data
}

export const getObligation = async (id) => {
  const response = await api.get(`/api/v1/obligations/${id}`)
  return response.data
}

export const completeObligation = async (id) => {
  const response = await api.patch(`/api/v1/obligations/${id}/complete`)
  return response.data
}

export const updateObligation = async (id, data) => {
  const response = await api.patch(`/api/v1/obligations/${id}`, data)
  return response.data
}

export const deleteObligation = async (id) => {
  const response = await api.delete(`/api/v1/obligations/${id}`)
  return response.data
}

export const getObligationStats = async () => {
  const response = await api.get('/api/v1/obligations/stats')
  return response.data
}