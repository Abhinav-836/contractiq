import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as obligationService from '../services/obligationService'

export const useObligations = (filters = {}) =>
  useQuery({
    queryKey: ['obligations', filters],
    queryFn: () => obligationService.getObligations(filters),
    staleTime: 5 * 60 * 1000,
  })

export const useObligation = (id) =>
  useQuery({
    queryKey: ['obligation', id],
    queryFn: () => obligationService.getObligation(id),
    enabled: !!id,
  })

export const useCompleteObligation = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: obligationService.completeObligation,
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ['obligations'] })
      qc.invalidateQueries({ queryKey: ['obligation', id] })
      qc.invalidateQueries({ queryKey: ['obligationStats'] })
    },
  })
}

export const useDeleteObligation = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: obligationService.deleteObligation,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['obligations'] })
      qc.invalidateQueries({ queryKey: ['obligationStats'] })
    },
  })
}

export const useObligationStats = () =>
  useQuery({
    queryKey: ['obligationStats'],
    queryFn: obligationService.getObligationStats,
    staleTime: 2 * 60 * 1000,
  })