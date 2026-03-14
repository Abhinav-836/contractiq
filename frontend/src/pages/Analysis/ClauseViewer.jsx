import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getContract, getContractAnalysis } from '../../services/contractService'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import Spinner from '../../components/ui/Spinner'

const riskColors = {
  high: { bg: '#EF4444', text: 'High Risk' },
  medium: { bg: '#F59E0B', text: 'Medium Risk' },
  low: { bg: '#10B981', text: 'Low Risk' }
}

export default function ClauseViewer() {
  const { id } = useParams()
  const navigate = useNavigate()

  const { data: contract, isLoading: contractLoading } = useQuery({
    queryKey: ['contract', id],
    queryFn: () => getContract(id),
  })

  const { data: analysis, isLoading: analysisLoading } = useQuery({
    queryKey: ['analysis', id],
    queryFn: () => getContractAnalysis(id),
    refetchInterval: (data) => {
      if (data?.status === 'processing') return 3000
      return false
    },
  })

  const isLoading = contractLoading || analysisLoading
  const isProcessing = analysis?.status === 'processing'

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 60 }}>
        <Spinner size="large" />
      </div>
    )
  }

  if (!analysis || isProcessing) {
    return (
      <div style={{ maxWidth: 800, margin: '0 auto', textAlign: 'center', padding: 60 }}>
        <Spinner size="large" />
        <h3 style={{ color: '#E2E8F0', marginTop: 20 }}>Analysis in Progress</h3>
        <p style={{ color: '#64748B', marginTop: 8 }}>
          Please wait while we analyze your contract.
        </p>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <button
        onClick={() => navigate('/analysis')}
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
        ← Back to Analysis
      </button>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontFamily: 'Sora,sans-serif', fontWeight: 700, fontSize: 24, color: '#E2E8F0', marginBottom: 8 }}>
            {contract?.filename || 'Contract Analysis'}
          </h1>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <Badge variant={analysis.risk_level}>
              {riskColors[analysis.risk_level]?.text}
            </Badge>
            <span style={{ color: '#64748B', fontSize: 13 }}>
              Risk Score: {analysis.risk_score}/100
            </span>
          </div>
        </div>
      </div>

      {/* Executive Summary */}
      <Card style={{ marginBottom: 24 }}>
        <h2 style={{ fontFamily: 'Sora,sans-serif', fontSize: 18, color: '#E2E8F0', marginBottom: 12 }}>
          Executive Summary
        </h2>
        <p style={{ color: '#94A3B8', lineHeight: 1.7, fontSize: 15 }}>
          {analysis.executive_summary || analysis.summary}
        </p>
      </Card>

      {/* All Clauses */}
      {analysis.clauses && analysis.clauses.length > 0 && (
        <Card style={{ marginBottom: 24 }}>
          <h2 style={{ fontFamily: 'Sora,sans-serif', fontSize: 18, color: '#E2E8F0', marginBottom: 16 }}>
            Clause Analysis ({analysis.clauses.length})
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {analysis.clauses.map((clause, index) => (
              <div
                key={index}
                style={{
                  padding: 20,
                  background: '#131B2A',
                  borderRadius: 12,
                  border: `1px solid ${
                    clause.risk_level === 'high' ? '#EF4444' :
                    clause.risk_level === 'medium' ? '#F59E0B' :
                    '#10B981'
                  }30`
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, color: '#E2E8F0' }}>
                    {clause.clause_type}
                  </h3>
                  <Badge variant={clause.risk_level}>
                    {clause.risk_level} risk
                  </Badge>
                </div>
                
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 13, color: '#64748B', marginBottom: 4 }}>Clause Text:</div>
                  <p style={{ color: '#94A3B8', fontSize: 14, lineHeight: 1.6, fontStyle: 'italic' }}>
                    "{clause.clause_text}"
                  </p>
                </div>

                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 13, color: '#64748B', marginBottom: 4 }}>Analysis:</div>
                  <p style={{ color: '#E2E8F0', fontSize: 14, lineHeight: 1.6 }}>
                    {clause.explanation}
                  </p>
                </div>

                {clause.recommendation && (
                  <div style={{ 
                    marginTop: 12, 
                    padding: 12, 
                    background: '#0F1623', 
                    borderRadius: 8,
                    borderLeft: '4px solid #00D4AA'
                  }}>
                    <span style={{ color: '#00D4AA', fontSize: 13, fontWeight: 600 }}>Recommendation: </span>
                    <span style={{ color: '#94A3B8', fontSize: 13 }}>{clause.recommendation}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Recommendations */}
      {analysis.recommendations && analysis.recommendations.length > 0 && (
        <Card>
          <h2 style={{ fontFamily: 'Sora,sans-serif', fontSize: 18, color: '#E2E8F0', marginBottom: 16 }}>
            Key Recommendations
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {analysis.recommendations.map((rec, index) => (
              <div key={index} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                <div style={{
                  width: 24,
                  height: 24,
                  borderRadius: 12,
                  background: '#00D4AA20',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#00D4AA',
                  fontSize: 14,
                  fontWeight: 600
                }}>
                  {index + 1}
                </div>
                <span style={{ color: '#94A3B8', fontSize: 15, lineHeight: 1.6, flex: 1 }}>{rec}</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}