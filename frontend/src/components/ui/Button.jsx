const VARIANTS = {
  primary: { background: '#00D4AA', color: '#080C14', border: 'none' },
  secondary: { background: '#1E2D3D', color: '#E2E8F0', border: '1px solid #2A3A4A' },
  outline: { background: 'transparent', color: '#00D4AA', border: '1px solid rgba(0,212,170,0.4)' },
  danger: { background: '#EF4444', color: '#fff', border: 'none' },
  ghost: { background: 'transparent', color: '#94A3B8', border: 'none' },
}

const SIZES = {
  small: { padding: '7px 14px', fontSize: 13 },
  medium: { padding: '9px 18px', fontSize: 14 },
  large: { padding: '12px 24px', fontSize: 15 },
}

export default function Button({
  children,
  onClick,
  disabled = false,
  type = 'button',
  variant = 'primary',
  size = 'medium',
  fullWidth = false,
  style = {},
}) {
  const v = VARIANTS[variant] || VARIANTS.primary
  const s = SIZES[size] || SIZES.medium

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      style={{
        ...v,
        ...s,
        borderRadius: 8,
        fontWeight: 700,
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        width: fullWidth ? '100%' : 'auto',
        fontFamily: 'inherit',
        transition: 'opacity 0.15s',
        ...style,
      }}
    >
      {children}
    </button>
  )
}