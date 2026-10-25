import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useObligation, useCompleteObligation } from '../../hooks/useObligations'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import Spinner from '../../components/ui/Spinner'
import { formatDate, formatDueDate } from '../../utils/formatters'
import toast from 'react-hot-toast'

export default function ObligationDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [isCompleting, setIsCompleting] = useState(false)

  const { data: obligation, isLoading } = useObligation(id)
  const completeMutation = useCompleteObligation()

  const handleComplete = async () => {
    setIsCompleting(true)
    try {
      await completeMutation.mutateAsync(id)
      toast.success('Obligation marked as completed!')
      navigate('/obligations')
    } catch {
      toast.error('Failed to complete obligation')
    } finally {
      setIsCompleting(false)
    }
  }

  if (isLoading) {
    return <div style={{ textAlign: 'center', padding: 60 }}><Spinner size="large" /></div>
  }

  if (!obligation) {
    return (
      <div style={{ textAlign: 'center', padding: 60 }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>❌</div>
        <h3 style={{ color: '#E2E8F0', marginBottom: 8 }}>Obligation not found</h3>
        <Button onClick={() => navigate('/obligations')}>Back to Obligations</Button>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <button
        onClick={() => navigate('/obligations')}
        style={{ background: 'none', border: 'none', color: '#64748B', cursor: 'pointer', fontSize: 14, marginBottom: 20, padding: 0 }}
      >
        ← Back to Obligations
      </button>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <Card style={{ padding: 32 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
            <Badge variant={obligation.status} size="large">{obligation.status}</Badge>
            <Badge variant={obligation.priority} size="large">{obligation.priority} priority</Badge>
          </div>

          <h1 style={{ fontFamily: 'Sora,sans-serif', fontWeight: 700, fontSize: 28, color: '#E2E8F0', marginBottom: 8 }}>
            {obligation.title}
          </h1>

          <p style={{ color: '#94A3B8', fontSize: 15, lineHeight: 1.7, marginBottom: 24 }}>
            {obligation.description || 'No description provided'}
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16, marginBottom: 24, padding: 20, background: '#131B2A', borderRadius: 12 }}>
            <div>
              <div style={{ fontSize: 12, color: '#64748B', marginBottom: 4 }}>Due Date</div>
              <div style={{ fontSize: 16, fontWeight: 600, color: obligation.status === 'overdue' ? '#EF4444' : '#E2E8F0' }}>
                {formatDueDate(obligation.dueDate)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: '#64748B', marginBottom: 4 }}>Assignee</div>
              <div style={{ fontSize: 16, fontWeight: 600, color: '#E2E8F0' }}>{obligation.assignedTo || 'Unassigned'}</div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: '#64748B', marginBottom: 4 }}>Created</div>
              <div style={{ fontSize: 16, fontWeight: 600, color: '#E2E8F0' }}>{formatDate(obligation.createdAt)}</div>
            </div>
          </div>

          {obligation.contractId && (
            <div style={{ marginBottom: 16 }}>
              <Button variant="outline" size="small" onClick={() => navigate(`/contracts/${obligation.contractId}`)}>
                📄 View source contract
              </Button>
            </div>
          )}

          {obligation.status !== 'completed' && (
            <Button onClick={handleComplete} disabled={isCompleting} fullWidth size="large">
              {isCompleting ? <Spinner size="small" /> : '✓ Mark as Completed'}
            </Button>
          )}

          {obligation.status === 'completed' && (
            <div style={{ textAlign: 'center', padding: 16, background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: 12, color: '#10B981' }}>
              ✓ This obligation has been completed
            </div>
          )}
        </Card>
      </motion.div>
    </div>
  )
}