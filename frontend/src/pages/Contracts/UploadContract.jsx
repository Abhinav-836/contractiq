import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useUploadContract } from '../../hooks/useContracts'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import toast from 'react-hot-toast'
import { getErrorMessage } from '../../utils/helpers'

export default function UploadContract() {
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [progress, setProgress] = useState(0)
  const inputRef = useRef()
  const uploadMutation = useUploadContract()

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true)
    else if (e.type === 'dragleave') setDragActive(false)
  }

  const validateAndSet = (f) => {
    const validTypes = ['.pdf', '.docx', '.txt']
    const ext = f.name.includes('.') ? '.' + f.name.split('.').pop().toLowerCase() : ''
    if (ext === '.doc') return toast.error('Legacy .doc files aren\'t supported — save as .docx or PDF')
    if (!validTypes.includes(ext)) return toast.error('Invalid file type. Use PDF, DOCX, or TXT')
    if (f.size === 0) return toast.error('File is empty')
    if (f.size > 20 * 1024 * 1024) return toast.error('File too large. Max 20MB')
    setFile(f)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    const f = e.dataTransfer.files[0]
    if (f) validateAndSet(f)
  }

  const handleUpload = async () => {
    if (!file) return
    try {
      setProgress(0)
      const result = await uploadMutation.mutateAsync({
        file,
        onProgress: setProgress,
      })
      toast.success('Contract uploaded! Analysis started.')
      navigate(`/contracts/${result.id}`)
    } catch (error) {
      toast.error(getErrorMessage(error, 'Upload failed'))
    }
  }

  const isUploading = uploadMutation.isPending

  return (
    <div style={{ maxWidth: 600, margin: '0 auto' }}>
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <button
          onClick={() => navigate('/contracts')}
          style={{ background: 'none', border: 'none', color: '#64748B', cursor: 'pointer', fontSize: 14, marginBottom: 20, padding: 0 }}
        >
          ← Back to Contracts
        </button>

        <h1 style={{ fontFamily: 'Sora,sans-serif', fontWeight: 700, fontSize: 28, color: '#E2E8F0', marginBottom: 8 }}>
          Upload Contract
        </h1>
        <p style={{ color: '#64748B', fontSize: 14, marginBottom: 32 }}>
          Upload a contract for AI-powered analysis. Text-based PDF, DOCX or TXT up to 50MB.
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
              opacity: isUploading ? 0.6 : 1,
            }}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={(e) => {
                if (e.target.files[0]) validateAndSet(e.target.files[0])
                e.target.value = '' // allow re-selecting the same file after an error
              }}
              style={{ display: 'none' }}
              disabled={isUploading}
            />
            <div style={{ fontSize: 48, marginBottom: 16 }}>{file ? '📄' : '📁'}</div>
            {file ? (
              <>
                <p style={{ color: '#00D4AA', fontWeight: 600, marginBottom: 4 }}>{file.name}</p>
                <p style={{ color: '#64748B', fontSize: 13 }}>{(file.size / 1024).toFixed(1)} KB</p>
              </>
            ) : (
              <>
                <p style={{ color: '#E2E8F0', fontWeight: 500, marginBottom: 8 }}>Upload a contract for AI-powered analysis. PDF (including scanned), DOCX or TXT up to 20MB.</p>
                <p style={{ color: '#64748B', fontSize: 13 }}>PDF, DOCX, TXT (max 20MB)</p>
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
                <div style={{ height: '100%', background: '#00D4AA', borderRadius: 99, width: `${progress}%`, transition: 'width 0.2s' }} />
              </div>
            </div>
          )}

          <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
            <Button variant="secondary" onClick={() => navigate('/contracts')} disabled={isUploading}>Cancel</Button>
            <Button onClick={handleUpload} disabled={!file || isUploading}>
              {isUploading ? 'Uploading...' : 'Upload & Analyze'}
            </Button>
          </div>
        </Card>
      </motion.div>
    </div>
  )
}