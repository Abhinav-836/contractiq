import { useState } from 'react'
const ALL=[
  {id:'1',type:'expiry',icon:'⏰',title:'Contract Expiring Soon',message:'Enterprise License with Acme Corp expires in 15 days.',read:false,time:'2 hours ago'},
  {id:'2',type:'risk',icon:'⚠️',title:'High Risk Detected',message:'Broad indemnification clause flagged in new vendor agreement.',read:false,time:'5 hours ago'},
  {id:'3',type:'obligation',icon:'✅',title:'Obligation Due',message:'Quarterly security audit due in 5 days per contract terms.',read:false,time:'1 day ago'},
  {id:'4',type:'renewal',icon:'🔄',title:'Renewal Notice',message:'Annual renewal window opens in 30 days for DataVault license.',read:true,time:'2 days ago'},
  {id:'5',type:'expiry',icon:'⏰',title:'Contract Expiring',message:'SLA with TechFlow expires in 22 days.',read:true,time:'3 days ago'},
  {id:'6',type:'risk',icon:'⚠️',title:'Risk Update',message:'New clause analysis complete for Vertex Group MSA.',read:true,time:'4 days ago'},
]
export default function AlertsPage(){
  const [alerts,setAlerts]=useState(ALL)
  const [filter,setFilter]=useState('all')
  const filtered=alerts.filter(a=>filter==='all'||(filter==='unread'&&!a.read)||a.type===filter)
  const markRead=id=>setAlerts(a=>a.map(x=>x.id===id?{...x,read:true}:x))
  const dismiss=id=>setAlerts(a=>a.filter(x=>x.id!==id))
  const markAll=()=>setAlerts(a=>a.map(x=>({...x,read:true})))
  const unread=alerts.filter(a=>!a.read).length
  return(
    <div style={{maxWidth:720,fontFamily:'DM Sans,sans-serif'}}>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:24}}>
        <div><h1 style={{fontFamily:'Sora,sans-serif',fontWeight:700,fontSize:24,color:'#E2E8F0',margin:0}}>Alerts</h1><p style={{color:unread>0?'#F59E0B':'#64748B',fontSize:14,marginTop:4}}>{unread>0?`${unread} unread`:'All caught up'}</p></div>
        {unread>0&&<button onClick={markAll} style={{padding:'9px 16px',borderRadius:8,border:'1px solid #1E2D3D',background:'none',color:'#CBD5E1',fontSize:13,cursor:'pointer'}}>✓ Mark all read</button>}
      </div>
      <div style={{display:'flex',gap:8,marginBottom:20,flexWrap:'wrap'}}>
        {['all','unread','expiry','obligation','risk','renewal'].map(f=>(
          <button key={f} onClick={()=>setFilter(f)} style={{padding:'8px 14px',borderRadius:8,border:`1px solid ${filter===f?'rgba(0,212,170,0.3)':'#1E2D3D'}`,background:filter===f?'rgba(0,212,170,0.1)':'none',color:filter===f?'#00D4AA':'#64748B',fontSize:13,cursor:'pointer',textTransform:'capitalize'}}>{f}</button>
        ))}
      </div>
      <div style={{display:'flex',flexDirection:'column',gap:10}}>
        {filtered.length===0&&<div style={{textAlign:'center',padding:60,color:'#64748B'}}>🔔 No alerts</div>}
        {filtered.map(a=>(
          <div key={a.id} style={{display:'flex',alignItems:'flex-start',gap:16,padding:20,background:'#0F1623',border:`1px solid ${a.read?'rgba(30,45,61,0.5)':'#1E2D3D'}`,borderRadius:12,opacity:a.read?0.65:1}}>
            <div style={{width:40,height:40,borderRadius:10,background:'rgba(255,255,255,0.05)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:20,flexShrink:0}}>{a.icon}</div>
            <div style={{flex:1,minWidth:0}}>
              <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:4}}>
                <span style={{fontSize:14,fontWeight:600,color:'#E2E8F0'}}>{a.title}</span>
                {!a.read&&<div style={{width:7,height:7,borderRadius:'50%',background:'#00D4AA'}}/>}
              </div>
              <p style={{fontSize:13,color:'#94A3B8',margin:'0 0 8px',lineHeight:1.5}}>{a.message}</p>
              <div style={{display:'flex',gap:16,alignItems:'center'}}>
                <span style={{fontSize:12,color:'#475569'}}>{a.time}</span>
                {!a.read&&<button onClick={()=>markRead(a.id)} style={{fontSize:12,color:'#00D4AA',background:'none',border:'none',cursor:'pointer',padding:0}}>Mark read</button>}
              </div>
            </div>
            <button onClick={()=>dismiss(a.id)} style={{background:'none',border:'none',color:'#475569',cursor:'pointer',fontSize:18,padding:'0 4px',lineHeight:1}}>×</button>
          </div>
        ))}
      </div>
    </div>
  )
}
