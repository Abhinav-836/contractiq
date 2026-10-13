import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as contractService from '../services/contractService'

export const useContracts = (params = {}) =>
  useQuery({
    queryKey: ['contracts', params],
    queryFn: () => contractService.getContracts(params),
  })

export const useContract = (id) =>
  useQuery({
    queryKey: ['contract', id],
    queryFn: () => contractService.getContract(id),
    enabled: !!id,
  })

export const useUploadContract = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ file, onProgress }) => contractService.uploadContract(file, onProgress),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['contracts'] }),
  })
}

export const useDeleteContract = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: contractService.deleteContract,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['contracts'] }),
  })
}