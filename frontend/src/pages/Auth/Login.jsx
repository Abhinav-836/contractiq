import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuthStore } from '../../store/authStore'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import Card from '../../components/ui/Card'
import Spinner from '../../components/ui/Spinner'

export default function Login() {
  const [form, setForm] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})
  const { login, isLoading, isAuthenticated } = useAuthStore()
  const navigate = useNavigate()

  const validateForm = () => {
    const next = {}
    if (!form.email) next.email = 'Email is required'
    else if (!/\S+@\S+\.\S+/.test(form.email)) next.email = 'Email is invalid'
    if (!form.password) next.password = 'Password is required'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validateForm()) return
    const result = await login(form.email, form.password)
    if (result.success) navigate('/dashboard')
  }

    if (isAuthenticated) return <Navigate to="/dashboard" replace />

  return (
    <div
      style={{
        position: 'relative',
        minHeight: '100vh',
        overflow: 'hidden',
        background: '#080C14',
      }}
    >
      {/* ─────────── Animated gradient background ─────────── */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 0,
          background: `
            radial-gradient(circle at 20% 25%, rgba(0,212,170,0.22), transparent 42%),
            radial-gradient(circle at 80% 15%, rgba(0,163,255,0.18), transparent 45%),
            radial-gradient(circle at 65% 85%, rgba(139,92,246,0.15), transparent 50%),
            radial-gradient(circle at 15% 90%, rgba(0,212,170,0.10), transparent 40%),
            #080C14
          `,
        }}
      />

      {/* Animated drifting orbs */}
      <motion.div
        aria-hidden
        animate={{
          x: [0, 40, 0],
          y: [0, -30, 0],
        }}
        transition={{ duration: 18, repeat: Infinity, ease: 'easeInOut' }}
        style={{
          position: 'absolute',
          top: '-10%',
          left: '-5%',
          width: 500,
          height: 500,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(0,212,170,0.25), transparent 70%)',
          filter: 'blur(40px)',
          zIndex: 0,
          pointerEvents: 'none',
        }}
      />
      <motion.div
        aria-hidden
        animate={{
          x: [0, -50, 0],
          y: [0, 40, 0],
        }}
        transition={{ duration: 22, repeat: Infinity, ease: 'easeInOut' }}
        style={{
          position: 'absolute',
          bottom: '-15%',
          right: '-10%',
          width: 600,
          height: 600,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(0,163,255,0.22), transparent 70%)',
          filter: 'blur(50px)',
          zIndex: 0,
          pointerEvents: 'none',
        }}
      />

      {/* Subtle grid overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 0,
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)
          `,
          backgroundSize: '48px 48px',
          maskImage:
            'radial-gradient(ellipse at center, rgba(0,0,0,0.6), transparent 75%)',
          WebkitMaskImage:
            'radial-gradient(ellipse at center, rgba(0,0,0,0.6), transparent 75%)',
        }}
      />

      {/* ─────────── Login form ─────────── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        style={{
          position: 'relative',
          zIndex: 1,
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 16,
        }}
      >
        <Card
          style={{
            maxWidth: 420,
            width: '100%',
            padding: 40,
            background: 'rgba(15,22,35,0.85)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            border: '1px solid rgba(0,212,170,0.15)',
            boxShadow:
              '0 20px 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(0,212,170,0.05), inset 0 1px 0 rgba(255,255,255,0.03)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              justifyContent: 'center',
              marginBottom: 32,
            }}
          >
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: 14,
                background: 'linear-gradient(135deg, #00D4AA 0%, #00A3FF 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 24,
                boxShadow:
                  '0 8px 32px rgba(0,212,170,0.4), inset 0 1px 0 rgba(255,255,255,0.2)',
              }}
            >
              ⚡
            </div>
            <span
              style={{
                fontFamily: 'Sora,sans-serif',
                fontWeight: 700,
                fontSize: 28,
                color: '#E2E8F0',
              }}
            >
              Contract
              <span
                style={{
                  color: '#00D4AA',
                  textShadow: '0 0 20px rgba(0,212,170,0.5)',
                }}
              >
                IQ
              </span>
            </span>
          </div>

          <h1
            style={{
              fontFamily: 'Sora,sans-serif',
              fontWeight: 700,
              fontSize: 28,
              color: '#E2E8F0',
              margin: '0 0 8px',
              textAlign: 'center',
            }}
          >
            Welcome back
          </h1>
          <p
            style={{
              color: '#64748B',
              fontSize: 14,
              marginBottom: 32,
              textAlign: 'center',
            }}
          >
            Sign in to access your AI-powered contract analysis
          </p>

          <form onSubmit={handleSubmit}>
            <Input
              label="Email address"
              type="email"
              placeholder="you@company.com"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              error={errors.email}
              autoComplete="email"
            />
            <div style={{ marginTop: 16 }}>
              <Input
                label="Password"
                type="password"
                placeholder="••••••••"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                error={errors.password}
                autoComplete="current-password"
              />
            </div>
            <div style={{ marginTop: 24 }}>
              <Button type="submit" disabled={isLoading} fullWidth>
                {isLoading ? <Spinner size="small" /> : 'Sign in →'}
              </Button>
            </div>
          </form>

          <p
            style={{
              textAlign: 'center',
              fontSize: 14,
              color: '#64748B',
              marginTop: 24,
            }}
          >
            No account?{' '}
            <Link
              to="/register"
              style={{
                color: '#00D4AA',
                textDecoration: 'none',
                fontWeight: 600,
              }}
            >
              Create one
            </Link>
          </p>
        </Card>
      </motion.div>
    </div>
  )
}