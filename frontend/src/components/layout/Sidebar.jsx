import { NavLink } from 'react-router-dom'
import { useUIStore } from '../../store/uiStore'
import { useQuery } from '@tanstack/react-query'
import { getAlertStats } from '../../services/alertService'

const NAV = [
  { to: '/dashboard', icon: '📊', label: 'Dashboard' },
  { to: '/contracts', icon: '📄', label: 'Contracts' },
  { to: '/analysis', icon: '🔍', label: 'Analysis' },
  { to: '/obligations', icon: '✅', label: 'Obligations' },
  { to: '/alerts', icon: '🔔', label: 'Alerts' },
]

export default function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useUIStore()
  
  // Get unread alerts count
  const { data: alertStats } = useQuery({
    queryKey: ['alertStats'],
    queryFn: getAlertStats,
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  const unreadAlerts = alertStats?.unread || 0
  const W = sidebarCollapsed ? 64 : 240

  return (
    <div style={{
      position: 'fixed', left: 0, top: 0, bottom: 0, width: W, zIndex: 40,
      background: '#0F1623', borderRight: '1px solid #1E2D3D',
      display: 'flex', flexDirection: 'column', transition: 'width 0.3s', overflow: 'hidden',
    }}>
      {/* Logo */}
      <div style={{ 
        padding: sidebarCollapsed ? '20px 0' : '20px 16px', 
        borderBottom: '1px solid #1E2D3D', 
        display: 'flex', 
        alignItems: 'center', 
        gap: 10, 
        justifyContent: sidebarCollapsed ? 'center' : 'flex-start' 
      }}>
        <div style={{ 
          width: 32, height: 32, borderRadius: 8, 
          background: 'linear-gradient(135deg, #00D4AA 0%, #00A3FF 100%)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', 
          flexShrink: 0, fontSize: 16, color: '#080C14'
        }}>
          ⚡
        </div>
        {!sidebarCollapsed && (
          <span style={{ 
            fontFamily: 'Sora,sans-serif', fontWeight: 700, fontSize: 18, 
            color: '#E2E8F0', whiteSpace: 'nowrap' 
          }}>
            Contract<span style={{ color: '#00D4AA' }}>IQ</span>
          </span>
        )}
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '12px 8px', overflowY: 'auto' }}>
        {NAV.map(({ to, icon, label }) => (
          <NavLink key={to} to={to} style={{ textDecoration: 'none' }}>
            {({ isActive }) => (
              <div style={{
                display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px',
                borderRadius: 8, marginBottom: 4, cursor: 'pointer',
                justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
                background: isActive ? 'rgba(0,212,170,0.1)' : 'transparent',
                border: `1px solid ${isActive ? 'rgba(0,212,170,0.2)' : 'transparent'}`,
                color: isActive ? '#00D4AA' : '#64748B',
                position: 'relative'
              }}>
                <span style={{ fontSize: 16 }}>{icon}</span>
                {!sidebarCollapsed && (
                  <>
                    <span style={{ 
                      fontSize: 14, fontWeight: 500, 
                      fontFamily: 'DM Sans,sans-serif', whiteSpace: 'nowrap' 
                    }}>
                      {label}
                    </span>
                    {label === 'Alerts' && unreadAlerts > 0 && (
                      <span style={{
                        position: 'absolute',
                        right: 8,
                        background: '#EF4444',
                        color: 'white',
                        fontSize: 11,
                        fontWeight: 600,
                        padding: '2px 6px',
                        borderRadius: 99,
                        minWidth: 18,
                        textAlign: 'center'
                      }}>
                        {unreadAlerts}
                      </span>
                    )}
                  </>
                )}
              </div>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Toggle */}
      <div style={{ padding: 8, borderTop: '1px solid #1E2D3D' }}>
        <button 
          onClick={toggleSidebar} 
          style={{
            width: '100%', padding: '10px 12px', borderRadius: 8, background: 'none', border: 'none',
            cursor: 'pointer', color: '#64748B', display: 'flex', alignItems: 'center', gap: 10,
            justifyContent: sidebarCollapsed ? 'center' : 'flex-start', fontSize: 14,
          }}
        >
          {sidebarCollapsed ? '→' : '← Collapse'}
        </button>
      </div>
    </div>
  )
}