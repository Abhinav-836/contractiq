import{forwardRef}from'react'
const Input=forwardRef(function Input({label,error,...props},ref){return(<div style={{display:'flex',flexDirection:'column',gap:6}}>{label&&<label style={{fontSize:13,fontWeight:500,color:'#CBD5E1'}}>{label}</label>}<input ref={ref} style={{padding:'10px 14px',background:'#080C14',border:`1px solid ${error?'rgba(239,68,68,0.5)':'#1E2D3D'}`,borderRadius:10,fontSize:14,color:'#E2E8F0',outline:'none',fontFamily:'DM Sans,sans-serif',...props.style}} {...props}/>{error&&<p style={{fontSize:12,color:'#F87171',margin:0}}>{error}</p>}</div>)})
export default Input
