import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import * as THREE from 'three'
import { useAuthStore } from '../../store/authStore'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import Card from '../../components/ui/Card'
import Spinner from '../../components/ui/Spinner'

export default function Login() {
  const [form, setForm] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})
  const { login, isLoading } = useAuthStore()
  const navigate = useNavigate()
  const canvasRef = useRef(null)
  const mousePosition = useRef({ x: 0, y: 0 })

  // Three.js Background Animation
  useEffect(() => {
    if (!canvasRef.current) return

    const scene = new THREE.Scene()
    scene.background = new THREE.Color('#080C14')
    
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
    camera.position.z = 30
    
    const renderer = new THREE.WebGLRenderer({ canvas: canvasRef.current, alpha: false })
    renderer.setSize(window.innerWidth, window.innerHeight)
    renderer.setPixelRatio(window.devicePixelRatio)

    // Create particles
    const particlesGeometry = new THREE.BufferGeometry()
    const particlesCount = 2000
    const posArray = new Float32Array(particlesCount * 3)
    const colorArray = new Float32Array(particlesCount * 3)

    for (let i = 0; i < particlesCount * 3; i += 3) {
      // Position
      posArray[i] = (Math.random() - 0.5) * 100
      posArray[i + 1] = (Math.random() - 0.5) * 100
      posArray[i + 2] = (Math.random() - 0.5) * 100

      // Color - teal with variations
      const color = new THREE.Color().setHSL(0.45 + Math.random() * 0.1, 0.8, 0.5)
      colorArray[i] = color.r
      colorArray[i + 1] = color.g
      colorArray[i + 2] = color.b
    }

    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3))
    particlesGeometry.setAttribute('color', new THREE.BufferAttribute(colorArray, 3))

    const particlesMaterial = new THREE.PointsMaterial({
      size: 0.1,
      vertexColors: true,
      transparent: true,
      opacity: 0.6,
      blending: THREE.AdditiveBlending
    })

    const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial)
    scene.add(particlesMesh)

    // Add floating cubes
    const cubes = []
    for (let i = 0; i < 5; i++) {
      const geometry = new THREE.BoxGeometry(0.5, 0.5, 0.5)
      const material = new THREE.MeshBasicMaterial({ 
        color: new THREE.Color().setHSL(0.45, 0.8, 0.5),
        transparent: true,
        opacity: 0.1,
        wireframe: true
      })
      const cube = new THREE.Mesh(geometry, material)
      cube.position.x = (Math.random() - 0.5) * 40
      cube.position.y = (Math.random() - 0.5) * 40
      cube.position.z = (Math.random() - 0.5) * 40
      cube.rotation.x = Math.random() * Math.PI
      cube.rotation.y = Math.random() * Math.PI
      scene.add(cube)
      cubes.push(cube)
    }

    // Mouse move handler
    const handleMouseMove = (e) => {
      mousePosition.current = {
        x: (e.clientX / window.innerWidth) * 2 - 1,
        y: -(e.clientY / window.innerHeight) * 2 + 1
      }
    }
    window.addEventListener('mousemove', handleMouseMove)

    // Animation
    const animate = () => {
      requestAnimationFrame(animate)

      // Rotate particles based on mouse
      particlesMesh.rotation.y += 0.0005
      particlesMesh.rotation.x += 0.0003

      // Animate cubes
      cubes.forEach((cube, i) => {
        cube.rotation.x += 0.002 * (i + 1)
        cube.rotation.y += 0.003 * (i + 1)
        
        // Mouse interaction
        cube.position.x += (mousePosition.current.x * 2 - cube.position.x) * 0.01
        cube.position.y += (mousePosition.current.y * 2 - cube.position.y) * 0.01
      })

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
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('resize', handleResize)
      renderer.dispose()
    }
  }, [])

  const validateForm = () => {
    const newErrors = {}
    if (!form.email) newErrors.email = 'Email is required'
    else if (!/\S+@\S+\.\S+/.test(form.email)) newErrors.email = 'Email is invalid'
    if (!form.password) newErrors.password = 'Password is required'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validateForm()) return

    const result = await login(form.email, form.password)
    if (result.success) {
      navigate('/dashboard')
    }
  }

  return (
    <div style={{ position: 'relative', minHeight: '100vh', overflow: 'hidden' }}>
      {/* Three.js Canvas */}
      <canvas
        ref={canvasRef}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          zIndex: 0
        }}
      />

      {/* Content */}
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
          background: 'rgba(8, 12, 20, 0.7)',
          backdropFilter: 'blur(10px)'
        }}
      >
        <Card style={{ maxWidth: 420, width: '100%', padding: 40 }}>
          <motion.div
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2 }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, justifyContent: 'center', marginBottom: 32 }}>
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: 14,
                  background: 'linear-gradient(135deg, #00D4AA 0%, #00A3FF 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 24,
                  boxShadow: '0 8px 32px rgba(0,212,170,0.3)'
                }}
              >
                ⚡
              </motion.div>
              <span style={{ fontFamily: 'Sora,sans-serif', fontWeight: 700, fontSize: 28, color: '#E2E8F0' }}>
                Contract<span style={{ color: '#00D4AA' }}>IQ</span>
              </span>
            </div>

            <motion.h1
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              style={{ fontFamily: 'Sora,sans-serif', fontWeight: 700, fontSize: 28, color: '#E2E8F0', margin: '0 0 8px', textAlign: 'center' }}
            >
              Welcome back
            </motion.h1>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              style={{ color: '#64748B', fontSize: 14, marginBottom: 32, textAlign: 'center' }}
            >
              Sign in to access your AI-powered contract analysis
            </motion.p>

            <form onSubmit={handleSubmit}>
              <motion.div
                initial={{ x: -20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ delay: 0.5 }}
              >
                <Input
                  label="Email address"
                  type="email"
                  placeholder="you@company.com"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  error={errors.email}
                  required
                />
              </motion.div>

              <motion.div
                initial={{ x: -20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ delay: 0.6 }}
                style={{ marginTop: 16 }}
              >
                <Input
                  label="Password"
                  type="password"
                  placeholder="••••••••"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  error={errors.password}
                  required
                />
              </motion.div>

              <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.7 }}
                style={{ marginTop: 24 }}
              >
                <Button
                  type="submit"
                  disabled={isLoading}
                  fullWidth
                >
                  {isLoading ? <Spinner /> : 'Sign in →'}
                </Button>
              </motion.div>
            </form>

            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
              style={{ textAlign: 'center', fontSize: 14, color: '#64748B', marginTop: 24 }}
            >
              No account?{' '}
              <Link
                to="/register"
                style={{
                  color: '#00D4AA',
                  textDecoration: 'none',
                  fontWeight: 600,
                  transition: 'color 0.2s'
                }}
                onMouseEnter={(e) => e.target.style.color = '#00ffcc'}
                onMouseLeave={(e) => e.target.style.color = '#00D4AA'}
              >
                Create one
              </Link>
            </motion.p>
          </motion.div>
        </Card>
      </motion.div>
    </div>
  )
}