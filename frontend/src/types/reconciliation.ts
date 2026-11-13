export interface SummaryCounts {
  exact_matches: number
  fuzzy_fee_matches: number
  reconciliation_exceptions: number
  orphan_transactions: number
  compliance_alerts: number
  [key: string]: number
}

export interface ReconciliationItem {
  payout_id?: string | number | null
  record_ids: string[]
  status: string
  reason: string
  details?: Record<string, any>
  rule_id?: string
  severity?: string
  description?: string
  payout_ids?: string[]
}

export interface ReconciliationReport {
  summary: SummaryCounts
  exact_matches: ReconciliationItem[]
  fuzzy_fee_matches: ReconciliationItem[]
  reconciliation_exceptions: ReconciliationItem[]
  orphan_transactions: ReconciliationItem[]
  compliance_alerts: ReconciliationItem[]
  generated_at?: string
  sources?: string[]
}

export interface SystemHealth {
  status: string
  version: string
  copilot_authenticated: boolean
  local_fixtures_available: boolean
}

export interface CopilotSession {
  session_id: string
  summary: string | null
  start_time: string
  modified_time: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  attachmentName?: string
}

