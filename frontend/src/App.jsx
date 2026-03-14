import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { queryClient } from './lib/queryClient'
import { PageLayout } from './components/layout/PageLayout'
import { ProtectedRoute } from './components/layout/ProtectedRoute'
import Login from './pages/Auth/Login'
import Register from './pages/Auth/Register'
import Dashboard from './pages/dashboard/Dashboard'
import ContractsPage from './pages/Contracts/ContractsPage'
import ContractDetail from './pages/Contracts/ContractDetail'
import UploadContract from './pages/Contracts/UploadContract'
import AnalysisPage from './pages/analysis/AnalysisPage'
import ClauseViewer from './pages/analysis/ClauseViewer'
import ObligationsPage from './pages/obligations/ObligationsPage'
import ObligationDetail from './pages/obligations/ObligationDetail'
import AlertsPage from './pages/alerts/AlertsPage'
import './styles/globals.css'

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Toaster 
          position="top-right"
          toastOptions={{
            style: {
              background: '#0F1623',
              color: '#E2E8F0',
              border: '1px solid #1E2D3D',
            },
            success: {
              iconTheme: {
                primary: '#00D4AA',
                secondary: '#0F1623',
              },
            },
            error: {
              iconTheme: {
                primary: '#EF4444',
                secondary: '#0F1623',
              },
            },
          }}
        />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<PageLayout />}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/contracts" element={<ContractsPage />} />
              <Route path="/contracts/:id" element={<ContractDetail />} />
              <Route path="/contracts/upload" element={<UploadContract />} />
              <Route path="/analysis" element={<AnalysisPage />} />
              <Route path="/analysis/:id" element={<ClauseViewer />} />
              <Route path="/obligations" element={<ObligationsPage />} />
              <Route path="/obligations/:id" element={<ObligationDetail />} />
              <Route path="/alerts" element={<AlertsPage />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
