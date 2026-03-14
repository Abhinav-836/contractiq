import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getContracts } from '../../services/contractService'

const rC = { high:'#EF4444', medium:'#F59E0B', low:'#10B981' }
const sC = { processing:'#8B5CF6', completed:'#10B981', failed:'#EF4444' }

export default function AnalysisPage() {
  const navigate = useNavigate()
  const [contracts, setContracts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    getContracts()
      .then(data => setContracts(Array.isArray(data) ? data : data?.contracts || []))
      .catch(() => setError('Failed to load contracts'))
      .finally(() => setLoading(false))
  }, [])

  const filtered = contracts.filter(c => filter === 'all' || c.risk_level === filter || c.status === filter)

  return (
    <div style={{ fontFamily:'DM Sans,sans-serif' }}>
      <h1 style={{ fontFamily:'Sora,sans-serif', fontWeight:700, fontSize:24, color:'#E2E8F0', marginBottom:6 }}>Analysis</h1>
      <p style={{ color:'#64748B', fontSize:14, marginBottom:24 }}>AI-powered contract analysis</p>

      {error && <div style={{ padding:'12px 16px', background:'rgba(239,68,68,0.1)', border:'1px solid rgba(239,68,68,0.2)', borderRadius:10, color:'#F87171', fontSize:14, marginBottom:16 }}>⚠️ {error}</div>}

      <div style={{ display:'flex', gap:8, marginBottom:20, flexWrap:'wrap' }}>
        {['all','high','medium','low','completed','processing'].map(f => (
          <button key={f} onClick={() => setFilter(f)} style={{ padding:'8px 14px', borderRadius:8, border:`1px solid ${filter===f ? 'rgba(0,212,170,0.3)':'#1E2D3D'}`, background:filter===f ? 'rgba(0,212,170,0.1)':'none', color:filter===f ? '#00D4AA':'#64748B', fontSize:13, cursor:'pointer', textTransform:'capitalize' }}>
            {f === 'all' ? 'All' : f}
          </button>
        ))}
      </div>

      {loading && <div style={{ textAlign:'center', padding:60, color:'#64748B' }}>Loading...</div>}

      {!loading && filtered.length === 0 && (
        <div style={{ textAlign:'center', padding:60, background:'#0F1623', border:'1px solid #1E2D3D', borderRadius:14 }}>
          <div style={{ fontSize:36, marginBottom:12 }}>📊</div>
          <p style={{ color:'#E2E8F0', marginBottom:6 }}>No analyses yet</p>
          <p style={{ color:'#64748B', fontSize:13, marginBottom:20 }}>Upload a contract to get AI analysis</p>
          <button onClick={() => navigate('/contracts/upload')} style={{ padding:'10px 20px', borderRadius:8, border:'none', background:'#00D4AA', color:'#080C14', fontSize:14, fontWeight:700, cursor:'pointer' }}>Upload Contract</button>
        </div>
      )}

      <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill,minmax(260px,1fr))', gap:16 }}>
        {!loading && filtered.map((c, i) => {
          const id = c.id || c.contract_id
          const name = c.filename || c.name || c.title || `Contract ${id}`
          return (
            <div key={id || i} onClick={() => navigate(`/analysis/${id}`)}
              style={{ background:'#0F1623', border:'1px solid #1E2D3D', borderRadius:14, padding:20, cursor:'pointer', transition:'border-color 0.2s' }}
              onMouseEnter={e => e.currentTarget.style.borderColor='rgba(0,212,170,0.3)'}
              onMouseLeave={e => e.currentTarget.style.borderColor='#1E2D3D'}>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:12 }}>
                <span style={{ fontSize:28 }}>📊</span>
                <div style={{ display:'flex', flexDirection:'column', gap:4, alignItems:'flex-end' }}>
                  {c.status && <span style={{ fontSize:11, color:sC[c.status]||'#64748B', background:`${sC[c.status]||'#64748B'}18`, padding:'2px 8px', borderRadius:99, textTransform:'capitalize' }}>{c.status}</span>}
                  {c.risk_level && <span style={{ fontSize:11, color:rC[c.risk_level], fontWeight:600 }}>{c.risk_level} risk</span>}
                </div>
              </div>
              <div style={{ fontWeight:600, fontSize:14, color:'#E2E8F0', marginBottom:4, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{name}</div>
              <div style={{ fontSize:12, color:'#475569', marginTop:8 }}>{c.created_at ? new Date(c.created_at).toLocaleDateString() : ''}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}