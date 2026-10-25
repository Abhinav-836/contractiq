import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getContract, getContractAnalysis } from '../../services/contractService'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import Spinner from '../../components/ui/Spinner'

export default function ClauseViewer() {
  const { id } = useParams()
  const navigate = useNavigate()

  const { data: contract, isLoading: contractLoading } = useQuery({
    queryKey: ['contract', id],
    queryFn: () => getContract(id),
    enabled: !!id,
    // Without polling this page sat on "Analysis in Progress" forever
    refetchInterval: (query) => (query.state.data?.status === 'processing' ? 3000 : false),
  })

  const { data: analysis, isLoading: analysisLoading } = useQuery({
    queryKey: ['analysis', id],
    queryFn: () => getContractAnalysis(id),
    enabled: !!id && contract?.status === 'completed',
  })

  if (contractLoading || (contract?.status === 'completed' && analysisLoading)) {
    return <div style={{ textAlign: 'center', padding: 60 }}><Spinner size="large" /></div>
  }

  if (!contract) {
    return (
      <div style={{ textAlign: 'center', padding: 60 }}>
        <h3 style={{ color: '#E2E8F0', marginBottom: 16 }}>Contract not found</h3>
        <Button onClick={() => navigate('/analysis')}>Back to Analysis</Button>
      </div>
    )
  }

  if (contract.status === 'processing') {
    return (
      <div style={{ maxWidth: 800, margin: '0 auto', textAlign: 'center', padding: 60 }}>
        <Spinner size="large" />
        <h3 style={{ color: '#E2E8F0', marginTop: 20 }}>Analysis in Progress</h3>
        <p style={{ color: '#64748B', marginTop: 8 }}>This page updates automatically.</p>
      </div>
    )
  }
  if (analysis?.risk_level === 'not_contract') {
    return (
      <div style={{ maxWidth: 800, margin: '0 auto', textAlign: 'center', padding: 60 }}>
        <div style={{ fontSize: 40, marginBottom: 12 }}>📄</div>
        <h3 style={{ color: '#E2E8F0', marginBottom: 8 }}>This doesn't look like a contract</h3>
        <p style={{ color: '#94A3B8', marginBottom: 20, lineHeight: 1.6 }}>
          {analysis.summary || 'No agreement terms were found in this document.'}
        </p>
        <Button onClick={() => navigate('/contracts/upload')}>Upload a contract</Button>
      </div>
    )
  }

  if (!analysis) {
    return (
      <div style={{ maxWidth: 800, margin: '0 auto', textAlign: 'center', padding: 60 }}>
        <div style={{ fontSize: 40, marginBottom: 12 }}>{contract.status === 'failed' ? '❌' : '📭'}</div>
        <h3 style={{ color: '#E2E8F0', marginBottom: 8 }}>
          {contract.status === 'failed' ? 'Analysis failed' : 'No analysis available'}
        </h3>
        <p style={{ color: '#64748B', marginBottom: 20 }}>You can retry the analysis from the contract page.</p>
        <Button onClick={() => navigate(`/contracts/${id}`)}>Open Contract</Button>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <button
        onClick={() => navigate(-1)}
        style={{ background: 'none', border: 'none', color: '#64748B', cursor: 'pointer', fontSize: 14, marginBottom: 20, padding: 0 }}
      >
        ← Back
      </button>

      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24, gap: 16, flexWrap: 'wrap' }}>
        <div>
          <h1 style={{ fontFamily: 'Sora,sans-serif', fontWeight: 700, fontSize: 24, color: '#E2E8F0', marginBottom: 8 }}>
            {contract.filename}
          </h1>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            {analysis.risk_level && <Badge variant={analysis.risk_level}>{analysis.risk_level} risk</Badge>}
            {analysis.risk_score != null && (
              <span style={{ color: '#64748B', fontSize: 13 }}>Risk Score: {analysis.risk_score}/100</span>
            )}
          </div>
        </div>
      </div>

      <Card style={{ marginBottom: 24 }}>
        <h2 style={{ fontFamily: 'Sora,sans-serif', fontSize: 18, color: '#E2E8F0', marginBottom: 12 }}>Executive Summary</h2>
        <p style={{ color: '#94A3B8', lineHeight: 1.7, fontSize: 15 }}>
          {analysis.executive_summary || analysis.summary || 'No summary available'}
        </p>
      </Card>

      {(analysis.parties?.length > 0 || analysis.key_dates?.length > 0) && (
        <Card style={{ marginBottom: 24 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 20 }}>
            {analysis.parties?.length > 0 && (
              <div>
                <h3 style={{ fontSize: 13, color: '#64748B', marginBottom: 8, fontWeight: 600 }}>Parties</h3>
                {analysis.parties.map((p, i) => (
                  <div key={i} style={{ color: '#E2E8F0', fontSize: 14, marginBottom: 4 }}>{p}</div>
                ))}
              </div>
            )}
            {analysis.key_dates?.length > 0 && (
              <div>
                <h3 style={{ fontSize: 13, color: '#64748B', marginBottom: 8, fontWeight: 600 }}>Key Dates</h3>
                {analysis.key_dates.map((d, i) => (
                  <div key={i} style={{ fontSize: 14, marginBottom: 4 }}>
                    <span style={{ color: '#94A3B8' }}>{d.label}: </span>
                    <span style={{ color: '#E2E8F0' }}>{d.date}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>
      )}

      {analysis.clauses?.length > 0 && (
        <Card style={{ marginBottom: 24 }}>
          <h2 style={{ fontFamily: 'Sora,sans-serif', fontSize: 18, color: '#E2E8F0', marginBottom: 16 }}>
            Clause Analysis ({analysis.clauses.length})
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {analysis.clauses.map((clause, i) => (
              <div
                key={i}
                style={{
                  padding: 20,
                  background: '#131B2A',
                  borderRadius: 12,
                  border: `1px solid ${clause.risk_level === 'high' ? '#EF4444' : clause.risk_level === 'medium' ? '#F59E0B' : '#10B981'}30`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, color: '#E2E8F0' }}>{clause.clause_type}</h3>
                  <Badge variant={clause.risk_level}>{clause.risk_level} risk</Badge>
                </div>
                {clause.clause_text && (
                  <div style={{ marginBottom: 12 }}>
                    <div style={{ fontSize: 13, color: '#64748B', marginBottom: 4 }}>Clause Text:</div>
                    <p style={{ color: '#94A3B8', fontSize: 14, lineHeight: 1.6, fontStyle: 'italic' }}>"{clause.clause_text}"</p>
                  </div>
                )}
                {clause.explanation && (
                  <div style={{ marginBottom: 12 }}>
                    <div style={{ fontSize: 13, color: '#64748B', marginBottom: 4 }}>Analysis:</div>
                    <p style={{ color: '#E2E8F0', fontSize: 14, lineHeight: 1.6 }}>{clause.explanation}</p>
                  </div>
                )}
                {clause.recommendation && (
                  <div style={{ marginTop: 12, padding: 12, background: '#0F1623', borderRadius: 8, borderLeft: '4px solid #00D4AA' }}>
                    <span style={{ color: '#00D4AA', fontSize: 13, fontWeight: 600 }}>Recommendation: </span>
                    <span style={{ color: '#94A3B8', fontSize: 13 }}>{clause.recommendation}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {analysis.recommendations?.length > 0 && (
        <Card>
          <h2 style={{ fontFamily: 'Sora,sans-serif', fontSize: 18, color: '#E2E8F0', marginBottom: 16 }}>Key Recommendations</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {analysis.recommendations.map((rec, i) => (
              <div key={i} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                <div style={{ width: 24, height: 24, borderRadius: 12, background: '#00D4AA20', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#00D4AA', fontSize: 14, fontWeight: 600, flexShrink: 0 }}>
                  {i + 1}
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