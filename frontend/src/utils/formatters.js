import { format, formatDistanceToNow, parseISO } from 'date-fns'

export const formatDate = (date, fmt = 'MMM d, yyyy') => {
  if (!date) return '—'
  try {
    const d = typeof date === 'string' ? parseISO(date) : date
    return format(d, fmt)
  } catch { return '—' }
}

export const formatRelativeTime = (date) => {
  if (!date) return '—'
  try {
    const d = typeof date === 'string' ? parseISO(date) : date
    return formatDistanceToNow(d, { addSuffix: true })
  } catch { return '—' }
}

export const formatCurrency = (amount, currency = 'USD') =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount ?? 0)

export const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

export const formatRiskScore = (score) => {
  if (score >= 75) return { label: 'High', color: 'danger' }
  if (score >= 40) return { label: 'Medium', color: 'warning' }
  return { label: 'Low', color: 'success' }
}

export const truncate = (str, maxLength = 80) =>
  str?.length > maxLength ? `${str.slice(0, maxLength)}...` : str ?? ''
// Add to existing file
export const formatObligationStatus = (status) => {
  const map = {
    pending: 'Pending',
    completed: 'Completed',
    overdue: 'Overdue',
    upcoming: 'Upcoming'
  }
  return map[status] || status
}

export const formatPriority = (priority) => {
  const map = {
    high: 'High Priority',
    medium: 'Medium Priority',
    low: 'Low Priority'
  }
  return map[priority] || priority
}

export const formatTimeRemaining = (dueDate) => {
  if (!dueDate) return 'No due date'
  
  const now = new Date()
  const due = new Date(dueDate)
  const diff = due - now
  const days = Math.ceil(diff / (1000 * 60 * 60 * 24))
  
  if (days < 0) return `${Math.abs(days)} days overdue`
  if (days === 0) return 'Due today'
  if (days === 1) return 'Due tomorrow'
  return `${days} days remaining`
}