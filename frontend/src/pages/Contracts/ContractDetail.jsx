import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getContract, getContractAnalysis, deleteContract, reanalyzeContract } from '../../services/contractService'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Spinner from '../../components/ui/Spinner'
import Badge from '../../components/ui/Badge'
import ConfirmDialog from '../../components/ui/ConfirmDialog'
import { formatDate } from '../../utils/formatters'
import toast from 'react-hot-toast'
import { getErrorMessage } from '../../utils/helpers'

const statusText = { processing: 'Analyzing', completed: 'Completed', failed: 'Failed' }

export default function ContractDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const [isRetrying, setIsRetrying] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const { data: contract, isLoading: contractLoading, error: contractError } = useQuery({
    queryKey: ['contract', id],
    queryFn: () => getContract(id),
    enabled: !!id,
    refetchInterval: (query) =>
      query.state.data?.status === 'processing' ? 3000 : false,
  })

  const { data: analysis, isLoading: analysisLoading } = useQuery({
    queryKey: ['analysis', id],
    queryFn: () => getContractAnalysis(id),
    enabled: !!id && contract?.status === 'completed',
  })

  // When analysis finishes, new obligations/alerts exist — refresh those views
  const prevStatus = useRef(contract?.status)
  useEffect(() => {
    if (prevStatus.current === 'processing' && contract?.status && contract.status !== 'processing') {
      invalidateLists()
    }
    prevStatus.current = contract?.status
  }, [contract?.status]) // eslint-disable-line react-hooks/exhaustive-deps

  const isLoading = contractLoading || (contract?.status === 'completed' && analysisLoading)
  const isProcessing = contract?.status === 'processing'

  const invalidateLists = () => {
    // every list/stat view that could still show this contract (all have 5-min staleTime)
    for (const key of ['contracts', 'contractStats', 'obligations', 'obligationStats', 'alerts', 'alertStats']) {
      qc.invalidateQueries({ queryKey: [key] })
    }
  }

  const handleRetry = async () => {
    setIsRetrying(true)
    try {
      await reanalyzeContract(id)
      qc.removeQueries({ queryKey: ['analysis', id] })
      await qc.invalidateQueries({ queryKey: ['contract', id] })
      invalidateLists()
      toast.success('Analysis restarted')
    } catch (err) {
      toast.error(getErrorMessage(err, 'Could not restart analysis'))
    } finally {
      setIsRetrying(false)
    }
  }

  const handleDelete = async () => {
    setIsDeleting(true)
    try {
      await deleteContract(id)
      qc.removeQueries({ queryKey: ['contract', id] })
      qc.removeQueries({ queryKey: ['analysis', id] })
      invalidateLists()
      toast.success('Contract deleted')
      navigate('/contracts')
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to delete contract'))
      setIsDeleting(false)
      setShowDeleteConfirm(false)
    }
  }

  if (isLoading && !contract) {
    return (
      <div style={{ textAlign: 'center', padding: 60 }}>
        <Spinner size="large" />
      </div>
    )
  }

  if (!contract && contractError?.response?.status !== 404 && contractError) {
    return (
      <div style={{ textAlign: 'center', padding: 60 }}>
        <h3 style={{ color: '#E2E8F0', marginBottom: 8 }}>Couldn't load this contract</h3>
        <p style={{ color: '#64748B', fontSize: 14, marginBottom: 20 }}>{getErrorMessage(contractError)}</p>
        <Button onClick={() => qc.invalidateQueries({ queryKey: ['contract', id] })}>Try again</Button>
      </div>
    )
  }

  if (!contract) {
    return (
      <div style={{ textAlign: 'center', padding: 60 }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>❌</div>
        <h3 style={{ color: '#E2E8F0', marginBottom: 8 }}>Contract not found</h3>
        <Button onClick={() => navigate('/contracts')}>Back to Contracts</Button>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <button
        onClick={() => navigate('/contracts')}
        style={{
          background: 'none',
          border: 'none',
          color: '#64748B',
          cursor: 'pointer',
          fontSize: 14,
          marginBottom: 20,
          padding: 0,
        }}
      >
        ← Back to Contracts
      </button>

      {/* Header with Delete button */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          marginBottom: 24,
          gap: 16,
          flexWrap: 'wrap',
        }}
      >
        <div>
          <h1
            style={{
              fontFamily: 'Sora,sans-serif',
              fontWeight: 700,
              fontSize: 24,
              color: '#E2E8F0',
              marginBottom: 8,
            }}
          >
            {contract.filename}
          </h1>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
            <Badge variant={contract.status}>
              {statusText[contract.status] || contract.status}
            </Badge>
            {contract.risk_level && (
              <Badge variant={contract.risk_level}>{contract.risk_level} risk</Badge>
            )}
            <span style={{ color: '#64748B', fontSize: 13 }}>
              Uploaded {formatDate(contract.created_at)}
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          {analysis && (
            <Button variant="outline" onClick={() => navigate(`/analysis/${id}`)}>
              View Full Analysis
            </Button>
          )}
          <Button variant="danger" onClick={() => setShowDeleteConfirm(true)}>
            🗑️ Delete
          </Button>
        </div>
      </div>

      {isProcessing && (
        <Card style={{ marginBottom: 24, padding: 32, textAlign: 'center' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
            <Spinner size="large" />
            <div>
              <h3 style={{ color: '#E2E8F0', marginBottom: 8 }}>AI Analysis in Progress</h3>
              <p style={{ color: '#64748B', fontSize: 14 }}>
                Please wait while we analyze your contract. This page will update automatically.
              </p>
            </div>
          </div>
        </Card>
      )}

      {analysis && (
        <>
          <Card style={{ marginBottom: 24 }}>
            <h2
              style={{
                fontFamily: 'Sora,sans-serif',
                fontSize: 18,
                color: '#E2E8F0',
                marginBottom: 12,
              }}
            >
              Executive Summary
            </h2>
            <p style={{ color: '#94A3B8', lineHeight: 1.7, fontSize: 14 }}>
              {analysis.executive_summary || analysis.summary || 'No summary available'}
            </p>
          </Card>

          {analysis.clauses?.length > 0 && (
            <Card style={{ marginBottom: 24 }}>
              <h2
                style={{
                  fontFamily: 'Sora,sans-serif',
                  fontSize: 18,
                  color: '#E2E8F0',
                  marginBottom: 16,
                }}
              >
                Key Clauses
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {analysis.clauses.slice(0, 3).map((clause, i) => (
                  <div
                    key={i}
                    style={{
                      padding: 16,
                      background: '#131B2A',
                      borderRadius: 8,
                      border: `1px solid ${
                        clause.risk_level === 'high'
                          ? '#EF4444'
                          : clause.risk_level === 'medium'
                          ? '#F59E0B'
                          : '#10B981'
                      }30`,
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: 8,
                      }}
                    >
                      <h3 style={{ fontSize: 15, fontWeight: 600, color: '#E2E8F0' }}>
                        {clause.clause_type}
                      </h3>
                      <Badge variant={clause.risk_level}>{clause.risk_level} risk</Badge>
                    </div>
                    <p style={{ color: '#94A3B8', fontSize: 13, marginBottom: 8 }}>
                      {clause.clause_text}
                    </p>
                    <p style={{ color: '#64748B', fontSize: 13 }}>{clause.explanation}</p>
                    {clause.recommendation && (
                      <div
                        style={{
                          marginTop: 8,
                          padding: 8,
                          background: '#0F1623',
                          borderRadius: 6,
                        }}
                      >
                        <span style={{ color: '#00D4AA', fontSize: 12, fontWeight: 600 }}>
                          Recommendation:{' '}
                        </span>
                        <span style={{ color: '#94A3B8', fontSize: 12 }}>
                          {clause.recommendation}
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              {analysis.clauses.length > 3 && (
                <div style={{ marginTop: 16, textAlign: 'center' }}>
                  <Button
                    variant="outline"
                    size="small"
                    onClick={() => navigate(`/analysis/${id}`)}
                  >
                    View All {analysis.clauses.length} Clauses
                  </Button>
                </div>
              )}
            </Card>
          )}

          {analysis.recommendations?.length > 0 && (
            <Card>
              <h2
                style={{
                  fontFamily: 'Sora,sans-serif',
                  fontSize: 18,
                  color: '#E2E8F0',
                  marginBottom: 16,
                }}
              >
                Recommendations
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {analysis.recommendations.map((rec, i) => (
                  <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                    <span style={{ color: '#00D4AA', fontSize: 16 }}>•</span>
                    <span style={{ color: '#94A3B8', fontSize: 14 }}>{rec}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}

      {contract.status === 'failed' && (
        <Card style={{ textAlign: 'center', padding: 40 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>❌</div>
          <h3 style={{ color: '#E2E8F0', marginBottom: 8 }}>Analysis Failed</h3>
          <p style={{ color: '#64748B', fontSize: 14, marginBottom: 20, maxWidth: 460, marginLeft: 'auto', marginRight: 'auto' }}>
            We couldn't extract readable text or the analysis was interrupted. Scanned/image-only
            PDFs aren't supported yet — use a text-based PDF, DOCX or TXT.
          </p>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button onClick={handleRetry} disabled={isRetrying}>
              {isRetrying ? 'Restarting...' : '↻ Retry Analysis'}
            </Button>
            <Button variant="outline" onClick={() => navigate('/contracts/upload')}>Upload Again</Button>
          </div>
        </Card>
      )}

      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => !isDeleting && setShowDeleteConfirm(false)}
        onConfirm={handleDelete}
        title="Delete contract?"
        message={
          contract
            ? `"${contract.filename}" and all its analysis, obligations, and alerts will be permanently deleted. This action cannot be undone.`
            : ''
        }
        confirmText="Delete"
        variant="danger"
        loading={isDeleting}
      />
    </div>
  )
}