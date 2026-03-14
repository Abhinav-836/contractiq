import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import { useUIStore } from '../../store/uiStore'

export function PageLayout() {
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed)
  const left = sidebarCollapsed ? 64 : 240
  return (
    <div style={{ minHeight:'100vh', background:'#080C14' }}>
      <Sidebar />
      <Topbar leftOffset={left} />
      <main style={{ marginLeft: left, paddingTop: 64, minHeight:'100vh', transition:'margin-left 0.3s' }}>
        <div style={{ padding: 24 }}>
          <Outlet />
        </div>
      </main>
    </div>
  )
}
