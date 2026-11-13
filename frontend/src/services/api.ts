import type {
  ReconciliationReport,
  SystemHealth,
  CopilotSession,
} from '../types/reconciliation'

const API_BASE = '/api'

export async function fetchHealth(): Promise<SystemHealth> {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error('Error al conectar con el backend')
  return res.json()
}

export async function runSamplesReconciliation(): Promise<{
  success: boolean
  sources: string[]
  report: ReconciliationReport
}> {
  const res = await fetch(`${API_BASE}/reconcile/run-samples`, {
    method: 'POST',
  })
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}))
    throw new Error(errorData.detail || 'Fallo al conciliar las muestras PoC')
  }
  return res.json()
}

export async function uploadAndReconcile(
  bankFile: File,
  gatewayFile: File,
  ledgerFile: File
): Promise<{
  success: boolean
  sources: string[]
  report: ReconciliationReport
}> {
  const formData = new FormData()
  formData.append('bank_file', bankFile)
  formData.append('gateway_file', gatewayFile)
  formData.append('ledger_file', ledgerFile)

  const res = await fetch(`${API_BASE}/reconcile/upload`, {
    method: 'POST',
    body: formData,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Error en la validación o procesamiento de reportes')
  }

  return res.json()
}

export async function downloadReportPdf(
  report: ReconciliationReport,
  sources: string[]
): Promise<Blob> {
  const res = await fetch(`${API_BASE}/reconcile/generate-pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ report, sources }),
  })

  if (!res.ok) {
    throw new Error('Error generando el PDF de conciliación')
  }

  return res.blob()
}

export async function fetchCopilotAuth(): Promise<{
  is_authenticated: boolean
  login: string | null
  auth_type: string | null
  status_message: string | null
}> {
  const res = await fetch(`${API_BASE}/copilot/auth`)
  return res.json()
}

export async function listCopilotSessions(): Promise<CopilotSession[]> {
  const res = await fetch(`${API_BASE}/copilot/sessions`)
  if (!res.ok) throw new Error('Error listando sesiones de Copilot')
  return res.json()
}

export async function createCopilotSession(
  name?: string,
  skills?: string[]
): Promise<{ session_id: string }> {
  const res = await fetch(`${API_BASE}/copilot/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, enabled_skills: skills }),
  })
  if (!res.ok) throw new Error('Error creando sesión')
  return res.json()
}

export async function sendChatMessage(
  sessionId: string,
  message: string,
  skills: string[],
  attachment?: File
): Promise<{ user_content: string; assistant_content: string }> {
  const formData = new FormData()
  formData.append('session_id', sessionId)
  formData.append('message', message)
  formData.append('skills', skills.join(','))
  if (attachment) {
    formData.append('attachment', attachment)
  }

  const res = await fetch(`${API_BASE}/copilot/chat`, {
    method: 'POST',
    body: formData,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Error procesando el mensaje con Copilot')
  }

  return res.json()
}

