import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

export default function Topbar({ leftOffset = 240 }) {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  return (
    <div style={{
      position:'fixed', top:0, left:leftOffset, right:0, height:64, zIndex:30,
      background:'rgba(15,22,35,0.95)', borderBottom:'1px solid #1E2D3D',
      display:'flex', alignItems:'center', justifyContent:'space-between',
      padding:'0 24px', transition:'left 0.3s',
    }}>
      <div style={{ display:'flex', alignItems:'center', gap:8, background:'#131B2A', border:'1px solid #1E2D3D', borderRadius:8, padding:'8px 12px', width:220 }}>
        <span style={{ color:'#64748B', fontSize:14 }}>🔍</span>
        <input placeholder="Search contracts..." style={{ background:'none', border:'none', outline:'none', color:'#E2E8F0', fontSize:14, width:'100%' }} />
      </div>

      <div style={{ position:'relative' }}>
        <button onClick={() => setOpen(!open)} style={{
          display:'flex', alignItems:'center', gap:8, background:'none', border:'none',
          cursor:'pointer', color:'#E2E8F0', padding:'6px 12px', borderRadius:8,
        }}>
          <div style={{ width:28, height:28, borderRadius:'50%', background:'rgba(0,212,170,0.15)', border:'1px solid rgba(0,212,170,0.3)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:14 }}>
            👤
          </div>
          <span style={{ fontSize:14, fontFamily:'DM Sans, sans-serif' }}>{user?.name || 'User'}</span>
          <span style={{ color:'#64748B' }}>▾</span>
        </button>

        {open && (
          <div style={{
            position:'absolute', right:0, top:'110%', width:180, background:'#131B2A',
            border:'1px solid #1E2D3D', borderRadius:12, overflow:'hidden', zIndex:50,
            boxShadow:'0 8px 32px rgba(0,0,0,0.5)',
          }}>
            <div style={{ padding:'12px 16px', borderBottom:'1px solid #1E2D3D' }}>
              <div style={{ fontSize:14, fontWeight:600, color:'#E2E8F0' }}>{user?.name}</div>
              <div style={{ fontSize:12, color:'#64748B' }}>{user?.email}</div>
            </div>
            <button onClick={() => { logout(); navigate('/login') }} style={{
              width:'100%', padding:'12px 16px', background:'none', border:'none',
              color:'#F87171', fontSize:14, cursor:'pointer', textAlign:'left', display:'flex', alignItems:'center', gap:8,
            }}>
              🚪 Sign out
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
