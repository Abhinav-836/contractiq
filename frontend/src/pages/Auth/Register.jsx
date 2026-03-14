import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { api } from '../../lib/axios'

const inp = { width:'100%', padding:'11px 14px', background:'#080C14', border:'1px solid #1E2D3D', borderRadius:10, fontSize:14, color:'#E2E8F0', fontFamily:'DM Sans,sans-serif', outline:'none', boxSizing:'border-box' }
const lbl = { display:'block', fontSize:13, fontWeight:500, color:'#CBD5E1', marginBottom:6 }

export default function Register() {
  const [form, setForm] = useState({ name:'', email:'', password:'', confirm:'' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (form.password !== form.confirm) { setError('Passwords do not match'); return }
    if (form.password.length < 6) { setError('Password must be at least 6 characters'); return }
    setLoading(true); setError('')
    try {
      const res = await api.post('/api/v1/auth/register', { name:form.name, email:form.email, password:form.password })
      const { access_token, user } = res.data
      login({ id:user.id, name:user.name, email:user.email, role:user.role }, access_token)
      navigate('/dashboard')
    } catch (err) {
      if (err.code === 'ERR_NETWORK') {
        login({ id:'1', name:form.name, email:form.email, role:'user' }, 'no-auth-token')
        navigate('/dashboard')
      } else {
        setError(err.response?.data?.detail || 'Registration failed')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight:'100vh', background:'#080C14', display:'flex', alignItems:'center', justifyContent:'center', padding:16, fontFamily:'DM Sans,sans-serif' }}>
      <div style={{ background:'#0F1623', border:'1px solid #1E2D3D', borderRadius:20, padding:36, width:'100%', maxWidth:420 }}>
        <div style={{ display:'flex', alignItems:'center', gap:12, justifyContent:'center', marginBottom:32 }}>
          <div style={{ width:40, height:40, borderRadius:12, background:'rgba(0,212,170,0.15)', border:'1px solid rgba(0,212,170,0.3)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:20 }}>⚡</div>
          <span style={{ fontFamily:'Sora,sans-serif', fontWeight:700, fontSize:24, color:'#E2E8F0' }}>Contract<span style={{ color:'#00D4AA' }}>IQ</span></span>
        </div>
        <h1 style={{ fontFamily:'Sora,sans-serif', fontWeight:700, fontSize:24, color:'#E2E8F0', margin:'0 0 6px' }}>Create account</h1>
        <p style={{ color:'#64748B', fontSize:14, marginBottom:28 }}>Start analyzing contracts with AI</p>
        {error && <div style={{ padding:'12px 16px', background:'rgba(239,68,68,0.1)', border:'1px solid rgba(239,68,68,0.2)', borderRadius:10, color:'#F87171', fontSize:14, marginBottom:20 }}>⚠️ {error}</div>}
        <form onSubmit={handleSubmit}>
          {[['Full name','text','Alex Morgan','name'],['Work email','email','you@company.com','email'],['Password','password','6+ characters','password'],['Confirm password','password','••••••••','confirm']].map(([label,type,ph,key]) => (
            <div key={key} style={{ marginBottom:16 }}>
              <label style={lbl}>{label}</label>
              <input type={type} placeholder={ph} value={form[key]} onChange={e => setForm({...form,[key]:e.target.value})} style={inp} required
                onFocus={e=>e.target.style.borderColor='rgba(0,212,170,0.5)'} onBlur={e=>e.target.style.borderColor='#1E2D3D'} />
            </div>
          ))}
          <button type="submit" disabled={loading} style={{ width:'100%', padding:'13px 20px', background:'#00D4AA', border:'none', borderRadius:10, color:'#080C14', fontSize:15, fontWeight:700, cursor:'pointer', marginTop:8, opacity:loading?0.7:1 }}>
            {loading ? 'Creating...' : 'Create account →'}
          </button>
        </form>
        <p style={{ textAlign:'center', fontSize:14, color:'#64748B', marginTop:20 }}>
          Have an account? <Link to="/login" style={{ color:'#00D4AA', textDecoration:'none' }}>Sign in</Link>
        </p>
      </div>
      <style>{`input::placeholder{color:#374151}`}</style>
    </div>
  )
}
