import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { QUERY_KEYS } from '../utils/constants'
import * as obligationService from '../services/obligationService'

export const useObligations = (filters = {}) => {
  return useQuery({
    queryKey: [QUERY_KEYS.OBLIGATIONS, filters],
    queryFn: () => obligationService.getObligations(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export const useObligation = (id) => {
  return useQuery({
    queryKey: [QUERY_KEYS.OBLIGATIONS, id],
    queryFn: () => obligationService.getObligation(id),
    enabled: !!id,
  })
}

export const useCompleteObligation = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: obligationService.completeObligation,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries([QUERY_KEYS.OBLIGATIONS])
      queryClient.invalidateQueries([QUERY_KEYS.OBLIGATIONS, id])
      queryClient.invalidateQueries([QUERY_KEYS.DASHBOARD])
    },
  })
}

export const useUpdateObligation = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }) => obligationService.updateObligation(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries([QUERY_KEYS.OBLIGATIONS])
      queryClient.invalidateQueries([QUERY_KEYS.OBLIGATIONS, id])
    },
  })
}

export const useDeleteObligation = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: obligationService.deleteObligation,
    onSuccess: () => {
      queryClient.invalidateQueries([QUERY_KEYS.OBLIGATIONS])
      queryClient.invalidateQueries([QUERY_KEYS.DASHBOARD])
    },
  })
}

export const useObligationStats = () => {
  return useQuery({
    queryKey: [QUERY_KEYS.OBLIGATIONS, 'stats'],
    queryFn: obligationService.getObligationStats,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}