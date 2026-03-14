import { create } from 'zustand'

export const useContractStore = create((set) => ({
  selectedContract: null,
  filters: { status: '', search: '', page: 1 },
  viewMode: 'table', // 'table' | 'card'

  setSelectedContract: (contract) => set({ selectedContract: contract }),
  setFilters: (filters) => set((state) => ({ filters: { ...state.filters, ...filters } })),
  resetFilters: () => set({ filters: { status: '', search: '', page: 1 } }),
  setViewMode: (mode) => set({ viewMode: mode }),
}))
