// src/pages/Contracts/UploadContract.jsx
import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useUploadContract } from '../../hooks/useContracts'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import toast from 'react-hot-toast'

export default function UploadContract() {
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const inputRef = useRef()
  
  const uploadMutation = useUploadContract()

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) validateAndSetFile(droppedFile)
  }

  const validateAndSetFile = (file) => {
    const validTypes = ['.pdf', '.doc', '.docx', '.txt']
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    
    if (!validTypes.includes(ext)) {
      toast.error('Invalid file type. Please upload PDF, DOC, DOCX, or TXT')
      return
    }
    
    if (file.size > 50 * 1024 * 1024) {
      toast.error('File too large. Maximum size is 50MB')
      return
    }
    
    setFile(file)
  }

  const handleUpload = async () => {
    if (!file) return
    
    try {
      const result = await uploadMutation.mutateAsync(file)
      toast.success('Contract uploaded successfully! Analysis started.')
      
      // Navigate to the new contract with cache-busting
      navigate(`/contracts/${result.id}?t=${Date.now()}`)
    } catch (error) {
      toast.error(error.response?.data?.detail || error.message || 'Upload failed')
    }
  }

  const progress = uploadMutation.data?.progress || 0
  const isUploading = uploadMutation.isPending

  return (
    <div style={{ maxWidth: 600, margin: '0 auto' }}>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <button
          onClick={() => navigate('/contracts')}
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
          ← Back to Contracts
        </button>

        <h1 style={{ fontFamily: 'Sora,sans-serif', fontWeight: 700, fontSize: 28, color: '#E2E8F0', marginBottom: 8 }}>
          Upload Contract
        </h1>
        <p style={{ color: '#64748B', fontSize: 14, marginBottom: 32 }}>
          Upload a contract for AI-powered analysis. We support PDF, DOC, DOCX, and TXT files up to 50MB.
        </p>

        <Card>
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => !isUploading && inputRef.current?.click()}
            style={{
              border: `2px dashed ${dragActive ? '#00D4AA' : file ? 'rgba(0,212,170,0.4)' : '#1E2D3D'}`,
              borderRadius: 12,
              padding: 48,
              textAlign: 'center',
              cursor: isUploading ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
              background: dragActive ? 'rgba(0,212,170,0.04)' : 'none',
              marginBottom: 24,
              opacity: isUploading ? 0.6 : 1
            }}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              onChange={(e) => e.target.files[0] && validateAndSetFile(e.target.files[0])}
              style={{ display: 'none' }}
              disabled={isUploading}
            />
            
            <div style={{ fontSize: 48, marginBottom: 16 }}>
              {file ? '📄' : '📁'}
            </div>
            
            {file ? (
              <>
                <p style={{ color: '#00D4AA', fontWeight: 600, marginBottom: 4 }}>
                  {file.name}
                </p>
                <p style={{ color: '#64748B', fontSize: 13 }}>
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </>
            ) : (
              <>
                <p style={{ color: '#E2E8F0', fontWeight: 500, marginBottom: 8 }}>
                  Drop your contract here or click to browse
                </p>
                <p style={{ color: '#64748B', fontSize: 13 }}>
                  PDF, DOC, DOCX, TXT (max 50MB)
                </p>
              </>
            )}
          </div>

          {isUploading && (
            <div style={{ marginBottom: 24 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: '#64748B', marginBottom: 8 }}>
                <span>Uploading...</span>
                <span style={{ color: '#00D4AA' }}>{progress}%</span>
              </div>
              <div style={{ height: 6, background: '#1E2D3D', borderRadius: 99 }}>
                <div
                  style={{
                    height: '100%',
                    background: '#00D4AA',
                    borderRadius: 99,
                    width: `${progress}%`,
                    transition: 'width 0.2s'
                  }}
                />
              </div>
            </div>
          )}

          <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
            <Button
              variant="secondary"
              onClick={() => navigate('/contracts')}
              disabled={isUploading}
            >
              Cancel
            </Button>
            <Button
              onClick={handleUpload}
              disabled={!file || isUploading}
            >
              {isUploading ? 'Uploading...' : 'Upload & Analyze'}
            </Button>
          </div>
        </Card>
      </motion.div>
    </div>
  )
}