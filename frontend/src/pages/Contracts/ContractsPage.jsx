import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getContracts, deleteContract } from '../../services/contractService'
import ConfirmDialog from '../../components/ui/ConfirmDialog'
import toast from 'react-hot-toast'
import { getErrorMessage } from '../../utils/helpers'

const sC = { processing: '#8B5CF6', completed: '#10B981', failed: '#EF4444' }
const rC = { high: '#EF4444', medium: '#F59E0B', low: '#10B981' }

export default function ContractsPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [contractToDelete, setContractToDelete] = useState(null)

  const { data: contracts = [], isLoading, error } = useQuery({
    queryKey: ['contracts', 'all'],
    queryFn: () => getContracts({ limit: 100 }),
    // only poll while something is still being analyzed
    refetchInterval: (query) =>
      query.state.data?.some((c) => c.status === 'processing') ? 5000 : false,
  })

  const deleteMutation = useMutation({
    mutationFn: deleteContract,
    onSuccess: () => {
      for (const key of ['contracts', 'contractStats', 'obligations', 'obligationStats', 'alerts', 'alertStats']) {
        qc.invalidateQueries({ queryKey: [key] })
      }
      toast.success('Contract deleted')
      setContractToDelete(null)
    },
    onError: (err) => {
      toast.error(getErrorMessage(err, 'Failed to delete contract'))
    },
  })

  const filtered = contracts.filter((c) => {
    const name = c.filename || ''
    return (
      (!status || c.status === status) &&
      (!search || name.toLowerCase().includes(search.toLowerCase()))
    )
  })

  const statuses = [...new Set(contracts.map((c) => c.status).filter(Boolean))]

  const handleDeleteClick = (e, contract) => {
    e.stopPropagation() // don't navigate to detail
    setContractToDelete(contract)
  }

  const handleConfirmDelete = () => {
    if (contractToDelete) deleteMutation.mutate(contractToDelete.id)
  }

  return (
    <div style={{ fontFamily: 'DM Sans,sans-serif' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontFamily: 'Sora,sans-serif', fontWeight: 700, fontSize: 24, color: '#E2E8F0', margin: 0 }}>
            Contracts
          </h1>
          <p style={{ color: '#64748B', fontSize: 14, marginTop: 4 }}>
            {isLoading ? 'Loading...' : `${filtered.length} contract${filtered.length !== 1 ? 's' : ''}`}
          </p>
        </div>
        <button
          onClick={() => navigate('/contracts/upload')}
          style={{ padding: '9px 18px', borderRadius: 8, border: 'none', background: '#00D4AA', color: '#080C14', fontSize: 14, fontWeight: 700, cursor: 'pointer' }}
        >
          ⬆ Upload Contract
        </button>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 10, color: '#F87171', fontSize: 14, marginBottom: 16 }}>
          ⚠️ Failed to load contracts
        </div>
      )}

      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        <input
          placeholder="Search contracts..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ padding: '9px 14px', background: '#0F1623', border: '1px solid #1E2D3D', borderRadius: 8, color: '#E2E8F0', fontSize: 14, outline: 'none', width: 220 }}
        />
        <button
          onClick={() => setStatus('')}
          style={{ padding: '9px 14px', borderRadius: 8, border: `1px solid ${!status ? 'rgba(0,212,170,0.3)' : '#1E2D3D'}`, background: !status ? 'rgba(0,212,170,0.1)' : 'none', color: !status ? '#00D4AA' : '#64748B', fontSize: 13, cursor: 'pointer' }}
        >
          All
        </button>
        {statuses.map((s) => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            style={{
              padding: '9px 14px',
              borderRadius: 8,
              border: `1px solid ${status === s ? `${sC[s] || '#64748B'}40` : '#1E2D3D'}`,
              background: status === s ? `${sC[s] || '#64748B'}15` : 'none',
              color: status === s ? sC[s] || '#64748B' : '#64748B',
              fontSize: 13,
              cursor: 'pointer',
              textTransform: 'capitalize',
            }}
          >
            {s === 'processing' ? 'Analyzing' : s}
          </button>
        ))}
      </div>

      <div style={{ background: '#0F1623', border: '1px solid #1E2D3D', borderRadius: 14, overflow: 'hidden' }}>
        {isLoading && <div style={{ textAlign: 'center', padding: 60, color: '#64748B' }}>Loading...</div>}

        {!isLoading && filtered.length === 0 && (
          <div style={{ textAlign: 'center', padding: 60 }}>
            <div style={{ fontSize: 36, marginBottom: 12 }}>📄</div>
            <p style={{ color: '#E2E8F0', marginBottom: 6 }}>No contracts found</p>
            <button
              onClick={() => navigate('/contracts/upload')}
              style={{ padding: '10px 20px', borderRadius: 8, border: 'none', background: '#00D4AA', color: '#080C14', fontSize: 14, fontWeight: 700, cursor: 'pointer', marginTop: 12 }}
            >
              Upload your first contract
            </button>
          </div>
        )}

        {!isLoading &&
          filtered.map((c, i) => (
            <div
              key={c.id}
              onClick={() => navigate(`/contracts/${c.id}`)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '14px 20px',
                borderBottom: i < filtered.length - 1 ? '1px solid #1E2D3D' : 'none',
                cursor: 'pointer',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = '#131B2A')}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 500, color: '#E2E8F0', marginBottom: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {c.filename}
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: 11, color: sC[c.status] || '#64748B', background: `${sC[c.status] || '#64748B'}18`, padding: '2px 8px', borderRadius: 99, textTransform: 'capitalize' }}>
                    {c.status === 'processing' ? 'Analyzing' : c.status}
                  </span>
                  {c.risk_level && <span style={{ fontSize: 11, color: rC[c.risk_level], fontWeight: 600 }}>{c.risk_level} risk</span>}
                  {c.file_type && <span style={{ fontSize: 11, color: '#475569' }}>{c.file_type.replace('.', '').toUpperCase()}</span>}
                </div>
              </div>

              {/* Right side: date/size + delete button */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0, marginLeft: 16 }}>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 12, color: '#475569' }}>
                    {c.created_at ? new Date(c.created_at).toLocaleDateString() : ''}
                  </div>
                  {c.file_size && (
                    <div style={{ fontSize: 11, color: '#374151', marginTop: 2 }}>
                      {Math.round(c.file_size / 1024)}KB
                    </div>
                  )}
                </div>

                <button
                  onClick={(e) => handleDeleteClick(e, c)}
                  title="Delete contract"
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: 8,
                    border: '1px solid transparent',
                    background: 'transparent',
                    color: '#64748B',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 15,
                    transition: 'all 0.15s',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'rgba(239,68,68,0.1)'
                    e.currentTarget.style.borderColor = 'rgba(239,68,68,0.3)'
                    e.currentTarget.style.color = '#EF4444'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'transparent'
                    e.currentTarget.style.borderColor = 'transparent'
                    e.currentTarget.style.color = '#64748B'
                  }}
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}
      </div>

      <ConfirmDialog
        isOpen={!!contractToDelete}
        onClose={() => setContractToDelete(null)}
        onConfirm={handleConfirmDelete}
        title="Delete contract?"
        message={
          contractToDelete
            ? `"${contractToDelete.filename}" and all its analysis, obligations, and alerts will be permanently deleted. This cannot be undone.`
            : ''
        }
        confirmText="Delete"
        variant="danger"
        loading={deleteMutation.isPending}
      />
    </div>
  )
}