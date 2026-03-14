// src/pages/Contracts/ContractDetail.jsx
import { useState, useEffect } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getContract, getContractAnalysis } from '../../services/contractService'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Spinner from '../../components/ui/Spinner'
import Badge from '../../components/ui/Badge'
import { formatDate } from '../../utils/formatters'

const statusColors = {
  processing: { bg: '#8B5CF6', text: 'Processing' },
  completed: { bg: '#10B981', text: 'Completed' },
  failed: { bg: '#EF4444', text: 'Failed' }
}

const riskColors = {
  high: { bg: '#EF4444', text: 'High Risk' },
  medium: { bg: '#F59E0B', text: 'Medium Risk' },
  low: { bg: '#10B981', text: 'Low Risk' }
}

export default function ContractDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()
  
  const queryParams = new URLSearchParams(location.search)
  const timestamp = queryParams.get('t')

  // Get contract details with cache busting
  const { data: contract, isLoading: contractLoading } = useQuery({
    queryKey: ['contract', id, timestamp],
    queryFn: () => getContract(id),
    staleTime: 0, // Always fetch fresh data
  })

  // Get analysis with proper polling
  const { data: analysis, isLoading: analysisLoading } = useQuery({
    queryKey: ['analysis', id, timestamp],
    queryFn: () => getContractAnalysis(id),
    refetchInterval: (query) => {
      const data = query.state.data
      // Stop polling if we have analysis or contract is completed/failed
      if (data || contract?.status === 'completed' || contract?.status === 'failed') {
        return false
      }
      return 3000 // Poll every 3 seconds while processing
    },
    enabled: !!id,
  })

  const isLoading = contractLoading || analysisLoading
  // Check if still processing - ONLY if contract status is processing AND no analysis yet
  const isProcessing = contract?.status === 'processing' && !analysis

  // Force refresh when analysis completes
  useEffect(() => {
    if (analysis) {
      // Invalidate contract query to refresh status
      queryClient.invalidateQueries({ queryKey: ['contract', id] })
    }
  }, [analysis, id, queryClient])

  if (isLoading && !contract) {
    return (
      <div style={{ textAlign: 'center', padding: 60 }}>
        <Spinner size="large" />
        <p style={{ color: '#64748B', marginTop: 16 }}>Loading contract details...</p>
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
          padding: 0
        }}
      >
        ← Back to Contracts
      </button>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontFamily: 'Sora,sans-serif', fontWeight: 700, fontSize: 24, color: '#E2E8F0', marginBottom: 8 }}>
            {contract.filename}
          </h1>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <Badge variant={contract.status}>
              {statusColors[contract.status]?.text || contract.status}
            </Badge>
            {contract.risk_level && (
              <Badge variant={contract.risk_level}>
                {riskColors[contract.risk_level]?.text}
              </Badge>
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
        </div>
      </div>

      {/* Processing State - Only show when actually processing */}
      {isProcessing && (
        <Card style={{ marginBottom: 24, padding: 32, textAlign: 'center' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
            <Spinner size="large" />
            <div>
              <h3 style={{ color: '#E2E8F0', marginBottom: 8 }}>AI Analysis in Progress</h3>
              <p style={{ color: '#64748B', fontSize: 14 }}>
                Please wait while we analyze your contract.<br />
                This page will update automatically.
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Analysis Results */}
      {analysis && !isProcessing && (
        <>
          {/* Executive Summary */}
          <Card style={{ marginBottom: 24 }}>
            <h2 style={{ fontFamily: 'Sora,sans-serif', fontSize: 18, color: '#E2E8F0', marginBottom: 12 }}>
              Executive Summary
            </h2>
            <p style={{ color: '#94A3B8', lineHeight: 1.7, fontSize: 14 }}>
              {analysis.executive_summary || analysis.summary || 'No summary available'}
            </p>
          </Card>

          {/* Key Clauses */}
          {analysis.clauses && analysis.clauses.length > 0 && (
            <Card style={{ marginBottom: 24 }}>
              <h2 style={{ fontFamily: 'Sora,sans-serif', fontSize: 18, color: '#E2E8F0', marginBottom: 16 }}>
                Key Clauses
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {analysis.clauses.slice(0, 3).map((clause, index) => (
                  <div
                    key={index}
                    style={{
                      padding: 16,
                      background: '#131B2A',
                      borderRadius: 8,
                      border: `1px solid ${
                        clause.risk_level === 'high' ? '#EF4444' :
                        clause.risk_level === 'medium' ? '#F59E0B' :
                        '#10B981'
                      }30`
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <h3 style={{ fontSize: 15, fontWeight: 600, color: '#E2E8F0' }}>
                        {clause.clause_type}
                      </h3>
                      <Badge variant={clause.risk_level}>
                        {clause.risk_level} risk
                      </Badge>
                    </div>
                    <p style={{ color: '#94A3B8', fontSize: 13, marginBottom: 8 }}>
                      {clause.clause_text}
                    </p>
                    <p style={{ color: '#64748B', fontSize: 13 }}>
                      {clause.explanation}
                    </p>
                    {clause.recommendation && (
                      <div style={{ marginTop: 8, padding: 8, background: '#0F1623', borderRadius: 6 }}>
                        <span style={{ color: '#00D4AA', fontSize: 12, fontWeight: 600 }}>Recommendation: </span>
                        <span style={{ color: '#94A3B8', fontSize: 12 }}>{clause.recommendation}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              {analysis.clauses.length > 3 && (
                <div style={{ marginTop: 16, textAlign: 'center' }}>
                  <Button variant="outline" size="small" onClick={() => navigate(`/analysis/${id}`)}>
                    View All {analysis.clauses.length} Clauses
                  </Button>
                </div>
              )}
            </Card>
          )}

          {/* Recommendations */}
          {analysis.recommendations && analysis.recommendations.length > 0 && (
            <Card>
              <h2 style={{ fontFamily: 'Sora,sans-serif', fontSize: 18, color: '#E2E8F0', marginBottom: 16 }}>
                Recommendations
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {analysis.recommendations.map((rec, index) => (
                  <div key={index} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                    <span style={{ color: '#00D4AA', fontSize: 16 }}>•</span>
                    <span style={{ color: '#94A3B8', fontSize: 14 }}>{rec}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}

      {/* Failed State */}
      {contract?.status === 'failed' && (
        <Card style={{ textAlign: 'center', padding: 40 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>❌</div>
          <h3 style={{ color: '#E2E8F0', marginBottom: 8 }}>Analysis Failed</h3>
          <p style={{ color: '#64748B', fontSize: 14, marginBottom: 20 }}>
            The analysis encountered an error. Please try uploading the contract again.
          </p>
          <Button onClick={() => navigate('/contracts/upload')}>
            Upload Again
          </Button>
        </Card>
      )}
    </div>
  )
}