import api from '../lib/axios'

export const uploadContract = async (file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post('/api/v1/contracts/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (e.total) onProgress?.(Math.round((e.loaded * 100) / e.total))
    },
  })
  return data
}

export const getContracts = async (params = {}) => {
  const qs = new URLSearchParams(params).toString()
  const { data } = await api.get(`/api/v1/contracts${qs ? `?${qs}` : ''}`)
  return Array.isArray(data) ? data : data?.contracts || []
}

export const getContract = async (id) => {
  const { data } = await api.get(`/api/v1/contracts/${id}`)
  return data
}

export const getContractAnalysis = async (contractId) => {
  try {
    const { data } = await api.get(`/api/v1/analysis/contract/${contractId}`)
    return data
  } catch (error) {
    if (error.response?.status === 404) return null
    throw error
  }
}

export const deleteContract = async (id) => {
  const { data } = await api.delete(`/api/v1/contracts/${id}`)
  return data
}

export const getContractStats = async () => {
  const { data } = await api.get('/api/v1/contracts/stats')
  return data
}