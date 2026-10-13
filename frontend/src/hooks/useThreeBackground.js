import { useEffect, useRef } from 'react'
import * as THREE from 'three'

export function useThreeBackground({
  particleCount = 400,
  mouseFollow = false,
  particleHue = 0.45,
} = {}) {
  const canvasRef = useRef(null)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    const canvas = canvasRef.current
    if (!canvas) return

    // ────────────────────────────────────────────────────────────
    // 1. Guard: verify WebGL is actually available before constructing
    // ────────────────────────────────────────────────────────────
    const testCtx =
      canvas.getContext('webgl2') ||
      canvas.getContext('webgl') ||
      canvas.getContext('experimental-webgl')

    if (!testCtx) {
      console.warn('[useThreeBackground] WebGL not supported — skipping')
      return
    }

    // ────────────────────────────────────────────────────────────
    // 2. Use the context we just verified (prevents double-init)
    // ────────────────────────────────────────────────────────────
    let renderer
    try {
      renderer = new THREE.WebGLRenderer({
        canvas,
        context: testCtx,
        alpha: false,
        antialias: false,
        powerPreference: 'low-power',
      })
    } catch (err) {
      console.warn('[useThreeBackground] WebGLRenderer init failed:', err)
      return
    }

    const width = canvas.clientWidth || window.innerWidth
    const height = canvas.clientHeight || window.innerHeight

    renderer.setSize(width, height, false)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))

    const scene = new THREE.Scene()
    scene.background = new THREE.Color('#080C14')

    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000)
    camera.position.z = 30

    // ────────────────────────────────────────────────────────────
    // 3. Particles
    // ────────────────────────────────────────────────────────────
    const geometry = new THREE.BufferGeometry()
    const positions = new Float32Array(particleCount * 3)
    const colors = new Float32Array(particleCount * 3)

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 80
      positions[i * 3 + 1] = (Math.random() - 0.5) * 80
      positions[i * 3 + 2] = (Math.random() - 0.5) * 50

      const c = new THREE.Color().setHSL(particleHue + Math.random() * 0.1, 0.8, 0.5)
      colors[i * 3] = c.r
      colors[i * 3 + 1] = c.g
      colors[i * 3 + 2] = c.b
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))

    const material = new THREE.PointsMaterial({
      size: 0.1,
      vertexColors: true,
      transparent: true,
      opacity: 0.5,
      blending: THREE.AdditiveBlending,
    })

    const particles = new THREE.Points(geometry, material)
    scene.add(particles)

    // ────────────────────────────────────────────────────────────
    // 4. Interaction & resize
    // ────────────────────────────────────────────────────────────
    const mouse = { x: 0, y: 0 }
    const handleMouse = (e) => {
      mouse.x = (e.clientX / window.innerWidth) * 2 - 1
      mouse.y = -(e.clientY / window.innerHeight) * 2 + 1
    }
    if (mouseFollow) window.addEventListener('mousemove', handleMouse)

    const handleResize = () => {
      if (!canvasRef.current) return
      const w = canvas.clientWidth || window.innerWidth
      const h = canvas.clientHeight || window.innerHeight
      camera.aspect = w / h
      camera.updateProjectionMatrix()
      renderer.setSize(w, h, false)
    }
    window.addEventListener('resize', handleResize)

    // ────────────────────────────────────────────────────────────
    // 5. Animation loop
    // ────────────────────────────────────────────────────────────
    let animId
    const animate = () => {
      if (!mountedRef.current) return
      animId = requestAnimationFrame(animate)
      particles.rotation.y += 0.0005
      if (mouseFollow) {
        particles.rotation.x += (mouse.y * 0.05 - particles.rotation.x) * 0.01
        particles.rotation.y += (mouse.x * 0.05 - particles.rotation.y) * 0.01
      }
      renderer.render(scene, camera)
    }
    animate()

    // ────────────────────────────────────────────────────────────
    // 6. Cleanup (StrictMode-safe)
    // ────────────────────────────────────────────────────────────
    return () => {
      mountedRef.current = false
      cancelAnimationFrame(animId)
      window.removeEventListener('resize', handleResize)
      if (mouseFollow) window.removeEventListener('mousemove', handleMouse)

      geometry.dispose()
      material.dispose()
      renderer.dispose()

      // Only force context loss if this is the REAL unmount (not StrictMode fake unmount)
      try {
        renderer.forceContextLoss?.()
      } catch {
        /* ignore */
      }
    }
  }, [particleCount, mouseFollow, particleHue])

  return canvasRef
}