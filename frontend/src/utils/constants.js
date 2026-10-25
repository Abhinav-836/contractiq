export const CONTRACT_STATUS = {
  DRAFT: 'draft',
  UNDER_REVIEW: 'under_review',
  ACTIVE: 'active',
  EXPIRED: 'expired',
  TERMINATED: 'terminated',
}

export const RISK_LEVELS = {
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low',
}

export const OBLIGATION_STATUS = {
  PENDING: 'pending',
  COMPLETED: 'completed',
  OVERDUE: 'overdue',
  UPCOMING: 'upcoming',
}

export const ALERT_TYPES = {
  EXPIRY: 'expiry',
  OBLIGATION: 'obligation',
  RISK: 'risk',
  RENEWAL: 'renewal',
}

export const CLAUSE_TYPES = [
  'Termination',
  'Liability',
  'Indemnification',
  'Confidentiality',
  'Payment Terms',
  'Intellectual Property',
  'Governing Law',
  'Force Majeure',
  'Warranties',
  'Dispute Resolution',
]

export const SUPPORTED_FILE_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
}

export const MAX_FILE_SIZE = 20 * 1024 * 1024 // 20MB

export const QUERY_KEYS = {
  CONTRACTS: 'contracts',
  CONTRACT: 'contract',
  ANALYSIS: 'analysis',
  OBLIGATIONS: 'obligations',
  ALERTS: 'alerts',
  DASHBOARD: 'dashboard',
  CHAT: 'chat',
}
