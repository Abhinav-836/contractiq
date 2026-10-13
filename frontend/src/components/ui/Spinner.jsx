const SIZES = {
  small: { size: 16, border: 2 },
  medium: { size: 20, border: 2 },
  large: { size: 40, border: 3 },
}

export default function Spinner({ size = 'medium' }) {
  const s = SIZES[size] || SIZES.medium
  return (
    <div
      style={{
        width: s.size,
        height: s.size,
        border: `${s.border}px solid #1E2D3D`,
        borderTopColor: '#00D4AA',
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
        display: 'inline-block',
      }}
    />
  )
}