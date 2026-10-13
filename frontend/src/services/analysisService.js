import api from '../lib/axios'

export const getAnalysisByContract = async (contractId) => {
  try {
    const { data } = await api.get(`/api/v1/analysis/contract/${contractId}`)
    return data
  } catch (error) {
    if (error.response?.status === 404) return null
    throw error
  }
}

export const getAnalysis = async (id) => {
  try {
    const { data } = await api.get(`/api/v1/analysis/${id}`)
    return data
  } catch (error) {
    if (error.response?.status === 404) return null
    throw error
  }
}