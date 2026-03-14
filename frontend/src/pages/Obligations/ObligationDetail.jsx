import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import * as THREE from 'three'
import { useObligation, useCompleteObligation } from '../../hooks/useObligations'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import Spinner from '../../components/ui/Spinner'
import { formatDate } from '../../utils/formatters'
import toast from 'react-hot-toast'

export default function ObligationDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const canvasRef = useRef(null)
  const [isCompleting, setIsCompleting] = useState(false)
  
  const { data: obligation, isLoading } = useObligation(id)
  const completeMutation = useCompleteObligation()

  // Three.js background
  useEffect(() => {
    if (!canvasRef.current) return

    const scene = new THREE.Scene()
    scene.background = new THREE.Color('#080C14')
    
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
    camera.position.z = 20
    
    const renderer = new THREE.WebGLRenderer({ canvas: canvasRef.current, alpha: false })
    renderer.setSize(window.innerWidth, window.innerHeight)
    renderer.setPixelRatio(window.devicePixelRatio)

    // Create focus ring
    const ringGeometry = new THREE.TorusGeometry(8, 0.1, 16, 100)
    const ringMaterial = new THREE.MeshBasicMaterial({ 
      color: 0x00d4aa,
      transparent: true,
      opacity: 0.1
    })
    const ring = new THREE.Mesh(ringGeometry, ringMaterial)
    ring.rotation.x = Math.PI / 2
    ring.rotation.z = Math.PI / 4
    scene.add(ring)

    // Add floating particles
    const particlesGeometry = new THREE.BufferGeometry()
    const particlesCount = 100
    const posArray = new Float32Array(particlesCount * 3)

    for (let i = 0; i < particlesCount; i++) {
      const radius = 10 + Math.random() * 5
      const angle = (i / particlesCount) * Math.PI * 2
      posArray[i * 3] = Math.cos(angle) * radius
      posArray[i * 3 + 1] = Math.sin(angle) * radius
      posArray[i * 3 + 2] = (Math.random() - 0.5) * 10
    }

    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3))
    const particlesMaterial = new THREE.PointsMaterial({
      size: 0.1,
      color: 0x00d4aa,
      transparent: true,
      opacity: 0.3
    })
    const particles = new THREE.Points(particlesGeometry, particlesMaterial)
    scene.add(particles)

    // Animation
    const animate = () => {
      requestAnimationFrame(animate)
      ring.rotation.z += 0.001
      particles.rotation.y += 0.0005
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

  const handleComplete = async () => {
    setIsCompleting(true)
    try {
      await completeMutation.mutateAsync(id)
      toast.success('Obligation marked as completed!')
      navigate('/obligations')
    } catch (error) {
      toast.error('Failed to complete obligation')
    } finally {
      setIsCompleting(false)
    }
  }

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 60 }}>
        <Spinner size="large" />
      </div>
    )
  }

  if (!obligation) {
    return (
      <div style={{ textAlign: 'center', padding: 60 }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>❌</div>
        <h3 style={{ color: '#E2E8F0', marginBottom: 8 }}>Obligation not found</h3>
        <Button onClick={() => navigate('/obligations')}>
          Back to Obligations
        </Button>
      </div>
    )
  }

  return (
    <div style={{ position: 'relative', minHeight: '100vh' }}>
      {/* Three.js Canvas */}
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
      <div style={{ position: 'relative', zIndex: 1, maxWidth: 800, margin: '0 auto' }}>
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <button
            onClick={() => navigate('/obligations')}
            style={{
              background: 'none',
              border: 'none',
              color: '#64748B',
              cursor: 'pointer',
              fontSize: 14,
              marginBottom: 20,
              padding: 0
            }}
          >
            ← Back to Obligations
          </button>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card style={{ padding: 32 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
              <Badge variant={obligation.status} size="large">
                {obligation.status}
              </Badge>
              <Badge variant={obligation.priority} size="large">
                {obligation.priority} priority
              </Badge>
            </div>

            <h1 style={{ fontFamily: 'Sora,sans-serif', fontWeight: 700, fontSize: 28, color: '#E2E8F0', marginBottom: 8 }}>
              {obligation.title}
            </h1>

            <p style={{ color: '#94A3B8', fontSize: 15, lineHeight: 1.7, marginBottom: 24 }}>
              {obligation.description || 'No description provided'}
            </p>

            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', 
              gap: 16,
              marginBottom: 24,
              padding: 20,
              background: '#131B2A',
              borderRadius: 12
            }}>
              <div>
                <div style={{ fontSize: 12, color: '#64748B', marginBottom: 4 }}>Due Date</div>
                <div style={{ fontSize: 16, fontWeight: 600, color: obligation.status === 'overdue' ? '#EF4444' : '#E2E8F0' }}>
                  {formatDate(obligation.dueDate)}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 12, color: '#64748B', marginBottom: 4 }}>Assignee</div>
                <div style={{ fontSize: 16, fontWeight: 600, color: '#E2E8F0' }}>
                  {obligation.assignee || 'Unassigned'}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 12, color: '#64748B', marginBottom: 4 }}>Contract</div>
                <div style={{ fontSize: 16, fontWeight: 600, color: '#E2E8F0' }}>
                  {obligation.contractName || 'Unknown'}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 12, color: '#64748B', marginBottom: 4 }}>Created</div>
                <div style={{ fontSize: 16, fontWeight: 600, color: '#E2E8F0' }}>
                  {formatDate(obligation.createdAt)}
                </div>
              </div>
            </div>

            {/* Progress section */}
            {obligation.progress !== undefined && (
              <div style={{ marginBottom: 24 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748B', fontSize: 14, marginBottom: 8 }}>
                  <span>Progress</span>
                  <span style={{ color: '#00D4AA' }}>{obligation.progress}%</span>
                </div>
                <div style={{ height: 8, background: '#1E2D3D', borderRadius: 4 }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${obligation.progress}%` }}
                    transition={{ duration: 1, delay: 0.3 }}
                    style={{ height: '100%', background: '#00D4AA', borderRadius: 4 }}
                  />
                </div>
              </div>
            )}

            {/* Action buttons */}
            {obligation.status !== 'completed' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <Button
                  onClick={handleComplete}
                  disabled={isCompleting}
                  fullWidth
                  size="large"
                >
                  {isCompleting ? <Spinner size="small" /> : '✓ Mark as Completed'}
                </Button>
              </motion.div>
            )}

            {obligation.status === 'completed' && (
              <div style={{ 
                textAlign: 'center', 
                padding: 16,
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.2)',
                borderRadius: 12,
                color: '#10B981'
              }}>
                ✓ This obligation has been completed
              </div>
            )}
          </Card>
        </motion.div>

        {/* Related obligations or notes could go here */}
        {obligation.notes && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            style={{ marginTop: 16 }}
          >
            <Card>
              <h3 style={{ color: '#E2E8F0', fontSize: 16, marginBottom: 12 }}>Notes</h3>
              <p style={{ color: '#94A3B8', fontSize: 14, lineHeight: 1.6 }}>{obligation.notes}</p>
            </Card>
          </motion.div>
        )}
      </div>
    </div>
  )
}