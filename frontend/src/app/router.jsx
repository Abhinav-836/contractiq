import { createBrowserRouter, Navigate, useRouteError, useNavigate } from 'react-router-dom'

// Lazy load every page so one broken import can't kill the whole app
import { lazy, Suspense } from 'react'

const Login = lazy(() => import('../pages/Auth/Login'))
const Register = lazy(() => import('../pages/Auth/Register'))
const Dashboard = lazy(() => import('../pages/Dashboard/Dashboard'))
const ContractsPage = lazy(() => import('../pages/Contracts/ContractsPage'))
const ContractDetail = lazy(() => import('../pages/Contracts/ContractDetail'))
const UploadContract = lazy(() => import('../pages/Contracts/UploadContract'))
const AnalysisPage = lazy(() => import('../pages/Analysis/AnalysisPage'))
const ClauseViewer = lazy(() => import('../pages/Analysis/ClauseViewer'))
const ObligationsPage = lazy(() => import('../pages/Obligations/ObligationsPage'))
const ObligationDetail = lazy(() => import('../pages/Obligations/ObligationDetail'))
const ChatPage = lazy(() => import('../pages/Chat/ChatPage'))
const AlertsPage = lazy(() => import('../pages/Alerts/AlertsPage'))

import { ProtectedRoute } from '../components/layout/ProtectedRoute'
import { PageLayout } from '../components/layout/PageLayout'

function Loading() {
  return (
    <div style={{ minHeight:'100vh', background:'#080C14', display:'flex', alignItems:'center', justifyContent:'center' }}>
      <div style={{ textAlign:'center' }}>
        <div style={{ width:36, height:36, border:'3px solid #1E2D3D', borderTopColor:'#00D4AA', borderRadius:'50%', animation:'spin 0.8s linear infinite', margin:'0 auto 16px' }} />
        <p style={{ color:'#64748B', fontSize:14, fontFamily:'sans-serif' }}>Loading...</p>
      </div>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
    </div>
  )
}

function ErrorPage() {
  const error = useRouteError()
  const navigate = useNavigate()
  return (
    <div style={{ minHeight:'100vh', background:'#080C14', display:'flex', alignItems:'center', justifyContent:'center', fontFamily:'sans-serif', padding:16 }}>
      <div style={{ background:'#0F1623', border:'1px solid #1E2D3D', borderRadius:16, padding:40, maxWidth:560, width:'100%', textAlign:'center' }}>
        <div style={{ fontSize:40, marginBottom:16 }}>⚠️</div>
        <h2 style={{ color:'#E2E8F0', marginBottom:8, fontSize:20 }}>
          {error?.status === 404 ? 'Page Not Found' : 'Something went wrong'}
        </h2>
        <p style={{ color:'#64748B', marginBottom:12, fontSize:14 }}>{error?.message || String(error)}</p>
        <pre style={{ color:'#F87171', fontSize:11, background:'#080C14', padding:12, borderRadius:8, marginBottom:20, textAlign:'left', overflow:'auto', maxHeight:180 }}>
          {error?.stack || JSON.stringify(error, null, 2)}
        </pre>
        <button onClick={() => navigate('/login')} style={{ padding:'10px 24px', background:'#00D4AA', color:'#080C14', border:'none', borderRadius:8, fontWeight:700, cursor:'pointer', fontSize:14 }}>
          Back to Login
        </button>
      </div>
    </div>
  )
}

function Wrap({ children }) {
  return <Suspense fallback={<Loading />}>{children}</Suspense>
}

export const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/login" replace /> },
  { path: '/login', element: <Wrap><Login /></Wrap>, errorElement: <ErrorPage /> },
  { path: '/register', element: <Wrap><Register /></Wrap>, errorElement: <ErrorPage /> },
  {
    element: <ProtectedRoute />,
    errorElement: <ErrorPage />,
    children: [{
      element: <PageLayout />,
      errorElement: <ErrorPage />,
      children: [
        { path: '/dashboard', element: <Wrap><Dashboard /></Wrap>, errorElement: <ErrorPage /> },
        { path: '/contracts', element: <Wrap><ContractsPage /></Wrap>, errorElement: <ErrorPage /> },
        { path: '/contracts/upload', element: <Wrap><UploadContract /></Wrap>, errorElement: <ErrorPage /> },
        { path: '/contracts/:id', element: <Wrap><ContractDetail /></Wrap>, errorElement: <ErrorPage /> },
        { path: '/analysis', element: <Wrap><AnalysisPage /></Wrap>, errorElement: <ErrorPage /> },
        { path: '/analysis/:id', element: <Wrap><ClauseViewer /></Wrap>, errorElement: <ErrorPage /> },
        { path: '/obligations', element: <Wrap><ObligationsPage /></Wrap>, errorElement: <ErrorPage /> },
        { path: '/obligations/:id', element: <Wrap><ObligationDetail /></Wrap>, errorElement: <ErrorPage /> },
        { path: '/chat', element: <Wrap><ChatPage /></Wrap>, errorElement: <ErrorPage /> },
        { path: '/alerts', element: <Wrap><AlertsPage /></Wrap>, errorElement: <ErrorPage /> },
        { path: '*', element: <Navigate to="/dashboard" replace /> },
      ],
    }],
  },
  { path: '*', element: <Navigate to="/login" replace /> },
])
