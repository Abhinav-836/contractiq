import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useObligations } from '../../hooks/useObligations'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Spinner from '../../components/ui/Spinner'
import { formatDueDate, dueDateSortKey } from '../../utils/formatters'

export default function ObligationsPage() {
  const navigate = useNavigate()
  const [filter, setFilter] = useState('all')
  const [sortBy, setSortBy] = useState('dueDate')

  const { data: obligations = [], isLoading } = useObligations()

  const stats = {
    overdue: obligations.filter((o) => o.status === 'overdue').length,
    pending: obligations.filter((o) => o.status === 'pending').length,
    total: obligations.length,
  }

  const filtered = obligations
    .filter((o) => filter === 'all' || o.status === filter)
    .slice() // don't mutate the react-query cache array
    .sort((a, b) => {
      if (sortBy === 'dueDate') return dueDateSortKey(a.dueDate) - dueDateSortKey(b.dueDate)
      if (sortBy === 'priority') {
        const w = { high: 3, medium: 2, low: 1 }
        return (w[b.priority] || 0) - (w[a.priority] || 0)
      }
      return 0
    })

  return (
    <div style={{ fontFamily: 'DM Sans,sans-serif' }}>
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: 32 }}>
        <h1 style={{ fontFamily: 'Sora,sans-serif', fontWeight: 700, fontSize: 28, color: '#E2E8F0', margin: 0 }}>Obligations</h1>
        <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
          <span style={{ color: '#EF4444', fontSize: 14 }}>{stats.overdue} overdue</span>
          <span style={{ color: '#F59E0B', fontSize: 14 }}>{stats.pending} pending</span>
          <span style={{ color: '#64748B', fontSize: 14 }}>{stats.total} total</span>
        </div>
      </motion.div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        {['all', 'overdue', 'pending', 'upcoming', 'completed'].map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            style={{
              padding: '8px 16px',
              borderRadius: 8,
              border: `1px solid ${filter === s ? 'rgba(0,212,170,0.3)' : '#1E2D3D'}`,
              background: filter === s ? 'rgba(0,212,170,0.1)' : 'none',
              color: filter === s ? '#00D4AA' : '#64748B',
              fontSize: 13,
              cursor: 'pointer',
              textTransform: 'capitalize',
            }}
          >
            {s === 'all' ? 'All' : s}
          </button>
        ))}
      </div>

      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          style={{ padding: '8px 12px', background: '#0F1623', border: '1px solid #1E2D3D', borderRadius: 8, color: '#E2E8F0', fontSize: 13, outline: 'none' }}
        >
          <option value="dueDate">Sort by Due Date</option>
          <option value="priority">Sort by Priority</option>
        </select>
      </div>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: 60 }}><Spinner size="large" /></div>
      ) : filtered.length === 0 ? (
        <Card style={{ textAlign: 'center', padding: 60 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
          <h3 style={{ color: '#E2E8F0', marginBottom: 8 }}>No obligations found</h3>
          <p style={{ color: '#64748B', fontSize: 14 }}>
            {filter === 'all' ? "You don't have any obligations yet" : `No ${filter} obligations found`}
          </p>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <AnimatePresence>
            {filtered.map((o, i) => (
              <motion.div
                key={o.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ delay: i * 0.03 }}
                whileHover={{ scale: 1.01 }}
                onClick={() => navigate(`/obligations/${o.id}`)}
                style={{
                  background: '#0F1623',
                  border: '1px solid #1E2D3D',
                  borderRadius: 12,
                  padding: 20,
                  cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
                      <Badge variant={o.status}>{o.status}</Badge>
                      <Badge variant={o.priority}>{o.priority} priority</Badge>
                    </div>
                    <h3 style={{ fontSize: 16, fontWeight: 600, color: '#E2E8F0', marginBottom: 4 }}>{o.title}</h3>
                    <p style={{ fontSize: 13, color: '#94A3B8', marginBottom: 8 }}>{o.description || 'No description'}</p>
                    <div style={{ display: 'flex', gap: 16, fontSize: 12, color: '#64748B', flexWrap: 'wrap' }}>
                      {o.assignedTo && <span>👤 {o.assignedTo}</span>}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right', marginLeft: 16 }}>
                    <div style={{ fontSize: 13, color: o.status === 'overdue' ? '#EF4444' : '#94A3B8', fontWeight: o.status === 'overdue' ? 600 : 400 }}>
                      {o.dueDate ? `Due: ${formatDueDate(o.dueDate)}` : 'No due date'}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}