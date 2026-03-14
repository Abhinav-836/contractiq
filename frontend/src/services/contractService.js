// src/services/contractService.js
import api from '../lib/axios'
import toast from 'react-hot-toast'

export const uploadContract = async (file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await api.post('/api/v1/contracts/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress?.(percentCompleted)
        }
      },
    })

    toast.success('Contract uploaded! Analysis started.')
    return response.data
  } catch (error) {
    if (error.response?.status === 413) {
      toast.error('File too large. Maximum size is 50MB')
    } else if (error.code === 'ERR_NETWORK') {
      toast.error('Network error. Please check if backend is running')
    } else {
      toast.error(error.response?.data?.detail || 'Upload failed')
    }
    throw error
  }
}

export const getContracts = async (params = {}) => {
  try {
    const queryParams = new URLSearchParams(params).toString()
    const response = await api.get(`/api/v1/contracts${queryParams ? `?${queryParams}` : ''}`)
    return response.data
  } catch (error) {
    console.error('Failed to load contracts:', error)
    return []
  }
}

export const getContract = async (id) => {
  try {
    const response = await api.get(`/api/v1/contracts/${id}`)
    return response.data
  } catch (error) {
    console.error('Failed to load contract:', error)
    throw error
  }
}

export const getContractAnalysis = async (id) => {
  try {
    const response = await api.get(`/api/v1/analysis/contract/${id}`)
    return response.data
  } catch (error) {
    if (error.response?.status === 404) {
      return null // Analysis not ready yet
    }
    console.error('Failed to load analysis:', error)
    throw error
  }
}

export const deleteContract = async (id) => {
  try {
    const response = await api.delete(`/api/v1/contracts/${id}`)
    toast.success('Contract deleted successfully')
    return response.data
  } catch (error) {
    toast.error('Failed to delete contract')
    throw error
  }
}

export const getContractStats = async () => {
  try {
    const response = await api.get('/api/v1/contracts/stats')
    return response.data
  } catch (error) {
    console.error('Failed to load stats:', error)
    return {
      total_contracts: 0,
      processing: 0,
      completed: 0,
      failed: 0,
      high_risk: 0,
      medium_risk: 0,
      low_risk: 0
    }
  }
}