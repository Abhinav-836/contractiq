import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { getContracts } from '../../services/contractService'
import { getObligationStats } from '../../services/obligationService'
import { getAlertStats } from '../../services/alertService'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Spinner from '../../components/ui/Spinner'
import { formatRelativeTime } from '../../utils/formatters'

const riskColors = {
  high: '#EF4444',
  medium: '#F59E0B',
  low: '#10B981'
}

const statusColors = {
  completed: '#10B981',
  processing: '#8B5CF6',
  failed: '#EF4444'
}

export default function Dashboard() {
  const navigate = useNavigate()

  const { data: contracts = [], isLoading: contractsLoading } = useQuery({
    queryKey: ['contracts'],
    queryFn: () => getContracts({ limit: 5 })
  })

  const { data: obligationStats, isLoading: obligationsLoading } = useQuery({
    queryKey: ['obligationStats'],
    queryFn: getObligationStats,
    refetchInterval: 30000
  })

  const { data: alertStats, isLoading: alertsLoading } = useQuery({
    queryKey: ['alertStats'],
    queryFn: getAlertStats,
    refetchInterval: 30000
  })

  const stats = [
    {
      label: 'Total Contracts',
      value: contracts.length,
      icon: '📄',
      color: '#00D4AA',
      loading: contractsLoading
    },
    {
      label: 'Pending Obligations',
      value: obligationStats?.pending || 0,
      icon: '✅',
      color: '#F59E0B',
      loading: obligationsLoading
    },
    {
      label: 'Overdue Tasks',
      value: obligationStats?.overdue || 0,
      icon: '⚠️',
      color: '#EF4444',
      loading: obligationsLoading
    },
    {
      label: 'Unread Alerts',
      value: alertStats?.unread || 0,
      icon: '🔔',
      color: '#8B5CF6',
      loading: alertsLoading
    }
  ]

  return (
    <div>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ marginBottom: 32 }}
      >
        <h1 style={{ fontFamily: 'Sora,sans-serif', fontWeight: 700, fontSize: 28, color: '#E2E8F0', marginBottom: 8 }}>
          Dashboard
        </h1>
        <p style={{ color: '#64748B', fontSize: 14 }}>
          Welcome back! Here's what's happening with your contracts.
        </p>
      </motion.div>

      {/* Stats Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: 20,
          marginBottom: 32
        }}
      >
        {stats.map((stat, index) => (
          <Card key={stat.label} hoverable>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{
                width: 48,
                height: 48,
                borderRadius: 12,
                background: `${stat.color}20`,
                border: `1px solid ${stat.color}40`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 24
              }}>
                {stat.icon}
              </div>
              <div>
                <p style={{ color: '#94A3B8', fontSize: 13, marginBottom: 4 }}>
                  {stat.label}
                </p>
                {stat.loading ? (
                  <Spinner size="small" />
                ) : (
                  <p style={{ color: '#E2E8F0', fontSize: 28, fontWeight: 700, margin: 0 }}>
                    {stat.value}
                  </p>
                )}
              </div>
            </div>
          </Card>
        ))}
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        style={{ marginBottom: 32 }}
      >
        <h2 style={{ fontFamily: 'Sora,sans-serif', fontWeight: 600, fontSize: 18, color: '#E2E8F0', marginBottom: 16 }}>
          Quick Actions
        </h2>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <Button onClick={() => navigate('/contracts/upload')}>
            📤 Upload New Contract
          </Button>
          <Button variant="outline" onClick={() => navigate('/obligations?status=pending')}>
            ✅ View Pending Obligations
          </Button>
          <Button variant="outline" onClick={() => navigate('/alerts')}>
            🔔 Check Alerts
            {alertStats?.unread > 0 && (
              <span style={{
                marginLeft: 8,
                background: '#EF4444',
                color: 'white',
                fontSize: 11,
                padding: '2px 6px',
                borderRadius: 99
              }}>
                {alertStats.unread}
              </span>
            )}
          </Button>
        </div>
      </motion.div>

      {/* Recent Contracts */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <h2 style={{ fontFamily: 'Sora,sans-serif', fontWeight: 600, fontSize: 18, color: '#E2E8F0', margin: 0 }}>
            Recent Contracts
          </h2>
          <Button variant="outline" size="small" onClick={() => navigate('/contracts')}>
            View All →
          </Button>
        </div>

        {contractsLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spinner />
          </div>
        ) : contracts.length === 0 ? (
          <Card style={{ textAlign: 'center', padding: 48 }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>📄</div>
            <h3 style={{ color: '#E2E8F0', marginBottom: 8 }}>No contracts yet</h3>
            <p style={{ color: '#64748B', fontSize: 14, marginBottom: 20 }}>
              Upload your first contract to get AI-powered analysis
            </p>
            <Button onClick={() => navigate('/contracts/upload')}>
              Upload Contract
            </Button>
          </Card>
        ) : (
          <Card>
            {contracts.map((contract, index) => (
              <div
                key={contract.id}
                onClick={() => navigate(`/contracts/${contract.id}`)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '16px 0',
                  borderBottom: index < contracts.length - 1 ? '1px solid #1E2D3D' : 'none',
                  cursor: 'pointer'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#131B2A'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{
                    width: 40,
                    height: 40,
                    borderRadius: 8,
                    background: contract.risk_level ? `${riskColors[contract.risk_level]}20` : '#1E2D3D',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 20
                  }}>
                    {contract.file_type === '.pdf' ? '📕' : '📄'}
                  </div>
                  <div>
                    <div style={{ fontWeight: 500, color: '#E2E8F0', marginBottom: 4 }}>
                      {contract.filename}
                    </div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <span style={{
                        fontSize: 11,
                        color: statusColors[contract.status] || '#64748B',
                        background: `${statusColors[contract.status] || '#64748B'}18`,
                        padding: '2px 8px',
                        borderRadius: 99,
                        textTransform: 'capitalize'
                      }}>
                        {contract.status}
                      </span>
                      {contract.risk_level && (
                        <span style={{
                          fontSize: 11,
                          color: riskColors[contract.risk_level],
                          fontWeight: 600
                        }}>
                          {contract.risk_level} risk
                        </span>
                      )}
                      <span style={{ fontSize: 11, color: '#475569' }}>
                        {formatRelativeTime(contract.created_at)}
                      </span>
                    </div>
                  </div>
                </div>
                <div style={{ color: '#475569', fontSize: 13 }}>
                  {contract.file_size ? `${Math.round(contract.file_size / 1024)} KB` : ''}
                </div>
              </div>
            ))}
          </Card>
        )}
      </motion.div>
    </div>
  )
}