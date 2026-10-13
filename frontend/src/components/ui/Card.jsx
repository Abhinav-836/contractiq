export default function Card({ children, style = {}, hoverable = false }) {
  return (
    <div
      style={{
        background: '#0F1623',
        border: '1px solid #1E2D3D',
        borderRadius: 14,
        padding: 20,
        transition: hoverable ? 'border-color 0.2s' : undefined,
        ...style,
      }}
      onMouseEnter={hoverable ? (e) => (e.currentTarget.style.borderColor = 'rgba(0,212,170,0.3)') : undefined}
      onMouseLeave={hoverable ? (e) => (e.currentTarget.style.borderColor = '#1E2D3D') : undefined}
    >
      {children}
    </div>
  )
}

export function CardHeader({ children }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
      {children}
    </div>
  )
}

export function CardTitle({ children }) {
  return (
    <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#E2E8F0', fontFamily: 'Sora,sans-serif' }}>
      {children}
    </h3>
  )
}