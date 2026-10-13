import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getAlerts, getAlertStats, markAlertRead, markAllAlertsRead, dismissAlert } from '../../services/alertService'
import toast from 'react-hot-toast'

const ICONS = { expiry: '⏰', risk: '⚠️', obligation: '✅', renewal: '🔄' }

export default function AlertsPage() {
  const [filter, setFilter] = useState('all')
  const qc = useQueryClient()

  const { data: alerts = [], isLoading } = useQuery({
    queryKey: ['alerts', filter],
    queryFn: () => getAlerts(filter === 'all' || filter === 'unread' ? {} : { type: filter }),
  })

  const { data: stats } = useQuery({
    queryKey: ['alertStats'],
    queryFn: getAlertStats,
  })

  const markRead = useMutation({
    mutationFn: markAlertRead,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['alerts'] })
      qc.invalidateQueries({ queryKey: ['alertStats'] })
    },
  })

  const markAll = useMutation({
    mutationFn: markAllAlertsRead,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['alerts'] })
      qc.invalidateQueries({ queryKey: ['alertStats'] })
      toast.success('All alerts marked as read')
    },
  })

  const dismiss = useMutation({
    mutationFn: dismissAlert,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['alerts'] })
      qc.invalidateQueries({ queryKey: ['alertStats'] })
    },
  })

  const filtered = alerts.filter((a) => {
    if (filter === 'all') return true
    if (filter === 'unread') return !a.read
    return a.type === filter
  })

  const unread = stats?.unread || 0

  return (
    <div style={{ maxWidth: 720, fontFamily: 'DM Sans,sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontFamily: 'Sora,sans-serif', fontWeight: 700, fontSize: 24, color: '#E2E8F0', margin: 0 }}>Alerts</h1>
          <p style={{ color: unread > 0 ? '#F59E0B' : '#64748B', fontSize: 14, marginTop: 4 }}>
            {unread > 0 ? `${unread} unread` : 'All caught up'}
          </p>
        </div>
        {unread > 0 && (
          <button
            onClick={() => markAll.mutate()}
            style={{ padding: '9px 16px', borderRadius: 8, border: '1px solid #1E2D3D', background: 'none', color: '#CBD5E1', fontSize: 13, cursor: 'pointer' }}
          >
            ✓ Mark all read
          </button>
        )}
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        {['all', 'unread', 'expiry', 'obligation', 'risk', 'renewal'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            style={{
              padding: '8px 14px',
              borderRadius: 8,
              border: `1px solid ${filter === f ? 'rgba(0,212,170,0.3)' : '#1E2D3D'}`,
              background: filter === f ? 'rgba(0,212,170,0.1)' : 'none',
              color: filter === f ? '#00D4AA' : '#64748B',
              fontSize: 13,
              cursor: 'pointer',
              textTransform: 'capitalize',
            }}
          >
            {f}
          </button>
        ))}
      </div>

      {isLoading && <div style={{ textAlign: 'center', padding: 60, color: '#64748B' }}>Loading...</div>}

      {!isLoading && filtered.length === 0 && (
        <div style={{ textAlign: 'center', padding: 60, color: '#64748B' }}>🔔 No alerts</div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {filtered.map((a) => (
          <div
            key={a.id}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 16,
              padding: 20,
              background: '#0F1623',
              border: `1px solid ${a.read ? 'rgba(30,45,61,0.5)' : '#1E2D3D'}`,
              borderRadius: 12,
              opacity: a.read ? 0.65 : 1,
            }}
          >
            <div style={{ width: 40, height: 40, borderRadius: 10, background: 'rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, flexShrink: 0 }}>
              {ICONS[a.type] || '🔔'}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <span style={{ fontSize: 14, fontWeight: 600, color: '#E2E8F0' }}>{a.title}</span>
                {!a.read && <div style={{ width: 7, height: 7, borderRadius: '50%', background: '#00D4AA' }} />}
              </div>
              <p style={{ fontSize: 13, color: '#94A3B8', margin: '0 0 8px', lineHeight: 1.5 }}>{a.message}</p>
              <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                <span style={{ fontSize: 12, color: '#475569' }}>
                  {a.createdAt ? new Date(a.createdAt).toLocaleString() : ''}
                </span>
                {!a.read && (
                  <button
                    onClick={() => markRead.mutate(a.id)}
                    style={{ fontSize: 12, color: '#00D4AA', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                  >
                    Mark read
                  </button>
                )}
              </div>
            </div>
            <button
              onClick={() => dismiss.mutate(a.id)}
              style={{ background: 'none', border: 'none', color: '#475569', cursor: 'pointer', fontSize: 18, padding: '0 4px', lineHeight: 1 }}
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}