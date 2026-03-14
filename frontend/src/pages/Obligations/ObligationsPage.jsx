import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import * as THREE from 'three'
import { useObligations } from '../../hooks/useObligations'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import Spinner from '../../components/ui/Spinner'
import { formatDate, formatRelativeTime } from '../../utils/formatters'

const statusColors = {
  pending: { bg: '#F59E0B20', text: '#F59E0B', border: '#F59E0B40' },
  completed: { bg: '#10B98120', text: '#10B981', border: '#10B98140' },
  overdue: { bg: '#EF444420', text: '#EF4444', border: '#EF444440' },
  upcoming: { bg: '#3B82F620', text: '#3B82F6', border: '#3B82F640' }
}

const priorityColors = {
  high: '#EF4444',
  medium: '#F59E0B',
  low: '#10B981'
}

export default function ObligationsPage() {
  const navigate = useNavigate()
  const canvasRef = useRef(null)
  const [filter, setFilter] = useState('all')
  const [sortBy, setSortBy] = useState('dueDate')
  const [stats, setStats] = useState({ overdue: 0, pending: 0, total: 0 })
  
  const { data: obligations = [], isLoading } = useObligations()

  // Keep the beautiful Three.js animation (it's visual, not technical)
  useEffect(() => {
    if (!canvasRef.current) return

    const scene = new THREE.Scene()
    scene.background = new THREE.Color('#080C14')
    
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
    camera.position.z = 30
    
    const renderer = new THREE.WebGLRenderer({ canvas: canvasRef.current, alpha: false })
    renderer.setSize(window.innerWidth, window.innerHeight)
    renderer.setPixelRatio(window.devicePixelRatio)

    // Create floating particles
    const particlesGeometry = new THREE.BufferGeometry()
    const particlesCount = 400
    const posArray = new Float32Array(particlesCount * 3)
    const colorArray = new Float32Array(particlesCount * 3)

    for (let i = 0; i < particlesCount; i++) {
      posArray[i * 3] = (Math.random() - 0.5) * 60
      posArray[i * 3 + 1] = (Math.random() - 0.5) * 60
      posArray[i * 3 + 2] = (Math.random() - 0.5) * 30

      const color = new THREE.Color().setHSL(0.45 + Math.random() * 0.2, 0.8, 0.5)
      colorArray[i * 3] = color.r
      colorArray[i * 3 + 1] = color.g
      colorArray[i * 3 + 2] = color.b
    }

    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3))
    particlesGeometry.setAttribute('color', new THREE.BufferAttribute(colorArray, 3))

    const particlesMaterial = new THREE.PointsMaterial({
      size: 0.1,
      vertexColors: true,
      transparent: true,
      opacity: 0.4,
      blending: THREE.AdditiveBlending
    })

    const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial)
    scene.add(particlesMesh)

    // Animation
    const animate = () => {
      requestAnimationFrame(animate)
      particlesMesh.rotation.y += 0.0002
      renderer.render(scene, camera)
    }
    animate()

    // Handle resize
    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight
      camera.updateProjectionMatrix()
      renderer.setSize(window.innerWidth, window.innerHeight)
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      renderer.dispose()
    }
  }, [])

  // Update stats when obligations change
  useEffect(() => {
    if (obligations.length) {
      setStats({
        overdue: obligations.filter(o => o.status === 'overdue').length,
        pending: obligations.filter(o => o.status === 'pending').length,
        total: obligations.length
      })
    }
  }, [obligations])

  // Filter and sort obligations
  const filtered = obligations
    .filter(o => filter === 'all' || o.status === filter)
    .sort((a, b) => {
      if (sortBy === 'dueDate') return new Date(a.dueDate) - new Date(b.dueDate)
      if (sortBy === 'priority') {
        const priorityWeight = { high: 3, medium: 2, low: 1 }
        return priorityWeight[b.priority] - priorityWeight[a.priority]
      }
      return 0
    })

  return (
    <div style={{ position: 'relative', minHeight: '100vh' }}>
      {/* Three.js Canvas - keeps the beautiful animation */}
      <canvas
        ref={canvasRef}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          zIndex: 0,
          pointerEvents: 'none'
        }}
      />

      {/* Content */}
      <div style={{ position: 'relative', zIndex: 1 }}>
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ marginBottom: 32 }}
        >
          <h1 style={{ fontFamily: 'Sora,sans-serif', fontWeight: 700, fontSize: 28, color: '#E2E8F0', margin: 0 }}>
            Obligations
          </h1>
          <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.1 }}
              style={{ color: '#EF4444', fontSize: 14 }}
            >
              {stats.overdue} overdue
            </motion.div>
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2 }}
              style={{ color: '#F59E0B', fontSize: 14 }}
            >
              {stats.pending} pending
            </motion.div>
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.3 }}
              style={{ color: '#64748B', fontSize: 14 }}
            >
              {stats.total} total
            </motion.div>
          </div>
        </motion.div>

        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}
        >
          {['all', 'overdue', 'pending', 'upcoming', 'completed'].map((status, i) => (
            <motion.button
              key={status}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.3 + i * 0.05 }}
              onClick={() => setFilter(status)}
              style={{
                padding: '8px 16px',
                borderRadius: 8,
                border: `1px solid ${filter === status ? 'rgba(0,212,170,0.3)' : '#1E2D3D'}`,
                background: filter === status ? 'rgba(0,212,170,0.1)' : 'none',
                color: filter === status ? '#00D4AA' : '#64748B',
                fontSize: 13,
                cursor: 'pointer',
                textTransform: 'capitalize'
              }}
            >
              {status === 'all' ? 'All' : status}
            </motion.button>
          ))}
        </motion.div>

        {/* Sort */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}
        >
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            style={{
              padding: '8px 12px',
              background: '#0F1623',
              border: '1px solid #1E2D3D',
              borderRadius: 8,
              color: '#E2E8F0',
              fontSize: 13,
              outline: 'none'
            }}
          >
            <option value="dueDate">Sort by Due Date</option>
            <option value="priority">Sort by Priority</option>
          </select>
        </motion.div>

        {/* Obligations List */}
        {isLoading ? (
          <div style={{ textAlign: 'center', padding: 60 }}>
            <Spinner size="large" />
          </div>
        ) : filtered.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
          >
            <Card style={{ textAlign: 'center', padding: 60 }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
              <h3 style={{ color: '#E2E8F0', marginBottom: 8 }}>No obligations found</h3>
              <p style={{ color: '#64748B', fontSize: 14 }}>
                {filter === 'all' 
                  ? "You don't have any obligations yet" 
                  : `No ${filter} obligations found`}
              </p>
            </Card>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            style={{ display: 'flex', flexDirection: 'column', gap: 12 }}
          >
            <AnimatePresence>
              {filtered.map((obligation, index) => (
                <motion.div
                  key={obligation.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.05 }}
                  whileHover={{ scale: 1.02, x: 10 }}
                  onClick={() => navigate(`/obligations/${obligation.id}`)}
                  style={{
                    background: 'rgba(15, 22, 35, 0.8)',
                    backdropFilter: 'blur(10px)',
                    border: `1px solid ${statusColors[obligation.status]?.border || '#1E2D3D'}`,
                    borderRadius: 12,
                    padding: 20,
                    cursor: 'pointer'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                        <Badge variant={obligation.status}>
                          {obligation.status}
                        </Badge>
                        <Badge variant={obligation.priority}>
                          {obligation.priority} priority
                        </Badge>
                      </div>
                      <h3 style={{ fontSize: 16, fontWeight: 600, color: '#E2E8F0', marginBottom: 4 }}>
                        {obligation.title}
                      </h3>
                      <p style={{ fontSize: 13, color: '#94A3B8', marginBottom: 8 }}>
                        {obligation.description || 'No description provided'}
                      </p>
                      <div style={{ display: 'flex', gap: 16, fontSize: 12, color: '#64748B' }}>
                        <span>📄 {obligation.contractName || 'Contract'}</span>
                        <span>👤 {obligation.assignee || 'Unassigned'}</span>
                      </div>
                    </div>
                    <div style={{ textAlign: 'right', marginLeft: 16 }}>
                      <div style={{ 
                        fontSize: 13, 
                        color: obligation.status === 'overdue' ? '#EF4444' : '#94A3B8',
                        fontWeight: obligation.status === 'overdue' ? 600 : 400,
                        marginBottom: 4
                      }}>
                        Due {formatDate(obligation.dueDate)}
                      </div>
                      <div style={{ fontSize: 11, color: '#475569' }}>
                        {formatRelativeTime(obligation.createdAt)}
                      </div>
                    </div>
                  </div>

                  {/* Progress bar for pending obligations */}
                  {obligation.status === 'pending' && obligation.progress && (
                    <div style={{ marginTop: 12 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#64748B', marginBottom: 4 }}>
                        <span>Progress</span>
                        <span>{obligation.progress}%</span>
                      </div>
                      <div style={{ height: 4, background: '#1E2D3D', borderRadius: 2 }}>
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${obligation.progress}%` }}
                          transition={{ duration: 1, delay: index * 0.1 }}
                          style={{ height: '100%', background: '#00D4AA', borderRadius: 2 }}
                        />
                      </div>
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
        )}
      </div>
    </div>
  )
}