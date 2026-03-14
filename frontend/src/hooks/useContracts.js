// src/hooks/useContracts.js
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as contractService from '../services/contractService'

export const useContracts = (params = {}) => {
  return useQuery({
    queryKey: ['contracts', params],
    queryFn: () => contractService.getContracts(params),
  })
}

export const useContract = (id) => {
  return useQuery({
    queryKey: ['contract', id],
    queryFn: () => contractService.getContract(id),
    enabled: !!id,
  })
}

export const useContractAnalysis = (id) => {
  return useQuery({
    queryKey: ['analysis', id],
    queryFn: () => contractService.getContractAnalysis(id),
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data
      // Stop polling if we have analysis data
      if (data) {
        return false
      }
      return 3000 // Poll every 3 seconds while waiting
    },
  })
}

export const useUploadContract = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (file) => {
      let progress = 0
      const result = await contractService.uploadContract(file, (p) => {
        progress = p
      })
      return { ...result, progress }
    },
    onSuccess: (data) => {
      // Invalidate all contract queries to refresh the list
      queryClient.invalidateQueries({ queryKey: ['contracts'] })
    },
  })
}

export const useDeleteContract = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: contractService.deleteContract,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] })
    },
  })
}