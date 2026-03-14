import { useState, useRef, useEffect } from 'react'

const RESPONSES=['Based on the contract, the termination clause requires 90 days notice with specific conditions for immediate termination in case of material breach.','The liability cap is set at 12 months contract value. I recommend negotiating for higher coverage given the project scope.','I found 3 high-risk clauses: broad indemnification, auto-renewal terms, and data privacy provisions that may conflict with GDPR.','Payment terms require net-30 invoicing with 1.5% monthly late fee. There is also a right-to-audit clause.','Per section 8.2, IP created during the engagement transfers to the client automatically. Ensure pre-existing IP is carved out.']
let ri=0

export default function ChatPage(){
  const [sessions,setSessions]=useState([{id:'1',title:'General Questions'}])
  const [activeId,setActiveId]=useState('1')
  const [messages,setMessages]=useState({'1':[]})
  const [input,setInput]=useState('')
  const [typing,setTyping]=useState(false)
  const bottomRef=useRef(null)

  useEffect(()=>{bottomRef.current?.scrollIntoView({behavior:'smooth'})},[messages,typing])

  const send=async(text)=>{
    if(!text.trim()||typing)return
    const msg={id:Date.now(),role:'user',content:text,time:new Date().toLocaleTimeString()}
    setMessages(m=>({...m,[activeId]:[...(m[activeId]||[]),msg]}))
    setInput(''); setTyping(true)
    await new Promise(r=>setTimeout(r,1000+Math.random()*800))
    const ai={id:Date.now()+1,role:'ai',content:RESPONSES[ri++%RESPONSES.length],time:new Date().toLocaleTimeString()}
    setMessages(m=>({...m,[activeId]:[...(m[activeId]||[]),ai]}))
    setTyping(false)
  }

  const newSession=()=>{
    const id=String(Date.now())
    setSessions(s=>[...s,{id,title:'New conversation'}])
    setMessages(m=>({...m,[id]:[]}))
    setActiveId(id)
  }

  const msgs=messages[activeId]||[]

  return(
    <div style={{display:'flex',height:'calc(100vh - 112px)',gap:0,fontFamily:'DM Sans,sans-serif'}}>
      {/* Sidebar */}
      <div style={{width:220,flexShrink:0,background:'#0F1623',border:'1px solid #1E2D3D',borderRadius:'14px 0 0 14px',display:'flex',flexDirection:'column'}}>
        <div style={{padding:12,borderBottom:'1px solid #1E2D3D'}}>
          <button onClick={newSession} style={{width:'100%',padding:'9px 12px',borderRadius:8,border:'1px solid #1E2D3D',background:'none',color:'#CBD5E1',fontSize:13,cursor:'pointer'}}>+ New Chat</button>
        </div>
        <div style={{flex:1,overflowY:'auto',padding:8}}>
          {sessions.map(s=>(
            <div key={s.id} onClick={()=>setActiveId(s.id)} style={{padding:'10px 12px',borderRadius:8,marginBottom:4,cursor:'pointer',background:activeId===s.id?'rgba(0,212,170,0.1)':'none',border:`1px solid ${activeId===s.id?'rgba(0,212,170,0.2)':'transparent'}`,color:activeId===s.id?'#00D4AA':'#64748B',fontSize:13}}>
              💬 {s.title}
            </div>
          ))}
        </div>
      </div>
      {/* Chat */}
      <div style={{flex:1,background:'rgba(15,22,35,0.5)',border:'1px solid #1E2D3D',borderLeft:'none',borderRadius:'0 14px 14px 0',display:'flex',flexDirection:'column',minWidth:0}}>
        <div style={{flex:1,overflowY:'auto',padding:20,display:'flex',flexDirection:'column',gap:16}}>
          {msgs.length===0&&(
            <div style={{display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',flex:1,textAlign:'center',paddingBottom:40}}>
              <div style={{fontSize:40,marginBottom:12}}>⚡</div>
              <h3 style={{color:'#E2E8F0',fontFamily:'Sora,sans-serif',marginBottom:8}}>Contract Intelligence AI</h3>
              <p style={{color:'#64748B',fontSize:14,maxWidth:280}}>Ask anything about your contracts — risk, obligations, key terms.</p>
              <div style={{display:'flex',flexDirection:'column',gap:8,marginTop:20,width:'100%',maxWidth:320}}>
                {['What are the high-risk clauses?','Summarize the payment terms','When does this contract expire?'].map(q=>(
                  <button key={q} onClick={()=>send(q)} style={{padding:'12px 16px',borderRadius:10,border:'1px solid #1E2D3D',background:'none',color:'#94A3B8',fontSize:13,cursor:'pointer',textAlign:'left'}}>
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
          {msgs.map(m=>(
            <div key={m.id} style={{display:'flex',justifyContent:m.role==='user'?'flex-end':'flex-start',gap:10}}>
              {m.role==='ai'&&<div style={{width:28,height:28,borderRadius:'50%',background:'rgba(0,212,170,0.15)',border:'1px solid rgba(0,212,170,0.3)',display:'flex',alignItems:'center',justifyContent:'center',flexShrink:0,fontSize:14}}>⚡</div>}
              <div style={{maxWidth:'75%',padding:'12px 16px',borderRadius:m.role==='user'?'16px 4px 16px 16px':'4px 16px 16px 16px',background:m.role==='user'?'rgba(0,212,170,0.1)':'#131B2A',border:`1px solid ${m.role==='user'?'rgba(0,212,170,0.2)':'#1E2D3D'}`,fontSize:14,color:'#CBD5E1',lineHeight:1.6}}>
                {m.content}
              </div>
            </div>
          ))}
          {typing&&<div style={{display:'flex',gap:10}}><div style={{width:28,height:28,borderRadius:'50%',background:'rgba(0,212,170,0.15)',border:'1px solid rgba(0,212,170,0.3)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:14}}>⚡</div><div style={{padding:'12px 16px',borderRadius:'4px 16px 16px 16px',background:'#131B2A',border:'1px solid #1E2D3D',color:'#64748B',fontSize:14}}>Analyzing...</div></div>}
          <div ref={bottomRef}/>
        </div>
        <div style={{padding:16,borderTop:'1px solid #1E2D3D'}}>
          <div style={{display:'flex',gap:10}}>
            <input value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send(input)}}} placeholder="Ask about your contracts..." disabled={typing}
              style={{flex:1,padding:'12px 16px',background:'#131B2A',border:'1px solid #1E2D3D',borderRadius:10,color:'#E2E8F0',fontSize:14,outline:'none',fontFamily:'DM Sans,sans-serif'}}/>
            <button onClick={()=>send(input)} disabled={!input.trim()||typing} style={{padding:'12px 20px',borderRadius:10,border:'none',background:input.trim()&&!typing?'#00D4AA':'#1E2D3D',color:input.trim()&&!typing?'#080C14':'#64748B',fontSize:14,fontWeight:700,cursor:'pointer'}}>Send</button>
          </div>
        </div>
      </div>
    </div>
  )
}
