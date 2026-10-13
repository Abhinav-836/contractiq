const COLORS = {
  success: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
  info: '#3B82F6',
  teal: '#00D4AA',
  default: '#64748B',
  // risk
  high: '#EF4444',
  medium: '#F59E0B',
  low: '#10B981',
  // status
  processing: '#8B5CF6',
  completed: '#10B981',
  failed: '#EF4444',
  pending: '#F59E0B',
  overdue: '#EF4444',
  upcoming: '#3B82F6',
}

export default function Badge({ children, variant = 'default', size = 'small' }) {
  const color = COLORS[variant] || COLORS.default
  const pad = size === 'large' ? '4px 12px' : '2px 8px'
  const fs = size === 'large' ? 13 : 11

  return (
    <span
      style={{
        fontSize: fs,
        fontWeight: 600,
        color,
        background: `${color}18`,
        padding: pad,
        borderRadius: 99,
        border: `1px solid ${color}25`,
        textTransform: 'capitalize',
        whiteSpace: 'nowrap',
        display: 'inline-block',
      }}
    >
      {children}
    </span>
  )
}