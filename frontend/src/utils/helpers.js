import { clsx } from 'clsx'

export const cn = (...inputs) => clsx(inputs)

export const sleep = (ms) => new Promise((res) => setTimeout(res, ms))

export const generateId = () => Math.random().toString(36).substr(2, 9)

export const getRiskColor = (level) => {
  const map = {
    high: 'text-red-400',
    medium: 'text-amber-400',
    low: 'text-emerald-400',
  }
  return map[level?.toLowerCase()] ?? 'text-slate-400'
}

export const getRiskBg = (level) => {
  const map = {
    high: 'bg-red-400/10 border-red-400/20',
    medium: 'bg-amber-400/10 border-amber-400/20',
    low: 'bg-emerald-400/10 border-emerald-400/20',
  }
  return map[level?.toLowerCase()] ?? 'bg-slate-400/10 border-slate-400/20'
}

export const getStatusColor = (status) => {
  const map = {
    active: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
    draft: 'text-slate-400 bg-slate-400/10 border-slate-400/20',
    under_review: 'text-blue-400 bg-blue-400/10 border-blue-400/20',
    expired: 'text-red-400 bg-red-400/10 border-red-400/20',
    terminated: 'text-red-500 bg-red-500/10 border-red-500/20',
    pending: 'text-amber-400 bg-amber-400/10 border-amber-400/20',
    completed: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
    overdue: 'text-red-400 bg-red-400/10 border-red-400/20',
    upcoming: 'text-blue-400 bg-blue-400/10 border-blue-400/20',
  }
  return map[status?.toLowerCase()] ?? 'text-slate-400 bg-slate-400/10 border-slate-400/20'
}

export const groupBy = (arr, key) =>
  arr.reduce((acc, item) => {
    const group = item[key]
    if (!acc[group]) acc[group] = []
    acc[group].push(item)
    return acc
  }, {})

export const debounce = (fn, delay) => {
  let timeout
  return (...args) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => fn(...args), delay)
  }
}
