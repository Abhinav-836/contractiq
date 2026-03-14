import api from '../lib/axios'
import toast from 'react-hot-toast'

export const getAnalyses = async () => {
  try {
    const response = await api.get('/api/v1/analysis')
    return response.data
  } catch (error) {
    console.error('Failed to fetch analyses:', error)
    return []
  }
}

export const getAnalysis = async (id) => {
  try {
    const response = await api.get(`/api/v1/analysis/${id}`)
    return response.data
  } catch (error) {
    if (error.response?.status === 404) {
      return null
    }
    console.error('Failed to fetch analysis:', error)
    throw error
  }
}

export const getContractAnalysis = async (contractId) => {
  try {
    const response = await api.get(`/api/v1/contracts/${contractId}/analysis`)
    return response.data
  } catch (error) {
    if (error.response?.status === 202) {
      return { status: 'processing', message: 'Analysis in progress' }
    }
    console.error('Failed to fetch contract analysis:', error)
    throw error
  }
}

export const getAnalysisClauses = async (analysisId) => {
  try {
    const response = await api.get(`/api/v1/analysis/${analysisId}/clauses`)
    return response.data
  } catch (error) {
    console.error('Failed to fetch clauses:', error)
    return []
  }
}

export const getAnalysisStats = async () => {
  try {
    const response = await api.get('/api/v1/analysis/stats')
    return response.data
  } catch (error) {
    console.error('Failed to fetch analysis stats:', error)
    return { total: 0, highRisk: 0, mediumRisk: 0, lowRisk: 0 }
  }
}