export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/dashboard',
  CONTRACTS: '/contracts',
  CONTRACT_DETAIL: '/contracts/:id',
  UPLOAD_CONTRACT: '/contracts/upload',
  ANALYSIS: '/analysis',
  ANALYSIS_DETAIL: '/analysis/:id',
  OBLIGATIONS: '/obligations',
  OBLIGATION_DETAIL: '/obligations/:id',
  CHAT: '/chat',
  ALERTS: '/alerts',
  SETTINGS: '/settings',
  PROFILE: '/profile',
  HELP: '/help'
}

export const NAVIGATION = [
  { to: ROUTES.DASHBOARD, icon: '📊', label: 'Dashboard' },
  { to: ROUTES.CONTRACTS, icon: '📄', label: 'Contracts' },
  { to: ROUTES.ANALYSIS, icon: '🔍', label: 'Analysis' },
  { to: ROUTES.OBLIGATIONS, icon: '✅', label: 'Obligations' },
  { to: ROUTES.CHAT, icon: '💬', label: 'AI Chat' },
  { to: ROUTES.ALERTS, icon: '🔔', label: 'Alerts' },
]