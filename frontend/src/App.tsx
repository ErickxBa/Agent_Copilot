import { useState, useEffect } from 'react'
import {
  Header,
} from './components/Header'
import {
  MetricCards,
} from './components/MetricCards'
import {
  Dropzone,
} from './components/Dropzone'
import {
  AuditTable,
} from './components/AuditTable'
import {
  AuditDrawer,
} from './components/AuditDrawer'
import {
  CopilotChat,
} from './components/CopilotChat'
import type {
  SystemHealth,
  ReconciliationReport,
  ReconciliationItem,
} from './types/reconciliation'
import {
  fetchHealth,
  runSamplesReconciliation,
  uploadAndReconcile,
  downloadReportPdf,
} from './services/api'
import {
  LayoutDashboard,
  MessageSquareCode,
  ShieldCheck,
  AlertCircle,
  FileCheck,
} from 'lucide-react'

export function App() {
  const [darkMode, setDarkMode] = useState(false)
  const [activeTab, setActiveTab] = useState<'reconciliation' | 'copilot'>('reconciliation')
  const [health, setHealth] = useState<SystemHealth | null>(null)
  
  // Reconciliation states
  const [report, setReport] = useState<ReconciliationReport | null>(null)
  const [sources, setSources] = useState<string[]>([])
  const [activeCategory, setActiveCategory] = useState('exact_matches')
  const [inspectedItem, setInspectedItem] = useState<{ item: ReconciliationItem; category: string } | null>(null)
  
  // Loading & status states
  const [loadingSamples, setLoadingSamples] = useState(false)
  const [loadingReconcile, setLoadingReconcile] = useState(false)
  const [downloadingPdf, setDownloadingPdf] = useState(false)
  const [notification, setNotification] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null)

  // Initialize theme & check backend health
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  useEffect(() => {
    checkHealth()
  }, [])

  const checkHealth = async () => {
    try {
      const res = await fetchHealth()
      setHealth(res)
    } catch (err: any) {
      console.warn('API health check error:', err.message)
    }
  }

  // Quick run with repository synthetic fixtures
  const handleRunSamples = async () => {
    setLoadingSamples(true)
    setNotification(null)
    try {
      const result = await runSamplesReconciliation()
      setReport(result.report)
      setSources(result.sources)
      setActiveCategory('exact_matches')
      setNotification({
        type: 'success',
        message: '¡Conciliación ejecutada con éxito usando las muestras sintéticas!',
      })
    } catch (err: any) {
      setNotification({
        type: 'error',
        message: 'Error al ejecutar las muestras: ' + err.message,
      })
    } finally {
      setLoadingSamples(false)
    }
  }

  // Upload and reconcile user files
  const handleUploadReconcile = async (bank: File, gateway: File, ledger: File) => {
    setLoadingReconcile(true)
    setNotification(null)
    try {
      const result = await uploadAndReconcile(bank, gateway, ledger)
      setReport(result.report)
      setSources(result.sources)
      setActiveCategory('exact_matches')
      setNotification({
        type: 'success',
        message: '¡Proceso completado! Se han cruzado los 3 archivos y generado el informe.',
      })
    } catch (err: any) {
      setNotification({
        type: 'error',
        message: 'Error en la conciliación: ' + err.message,
      })
    } finally {
      setLoadingReconcile(false)
    }
  }

  // Download PDF audit report
  const handleDownloadPdf = async () => {
    if (!report) return
    setDownloadingPdf(true)
    try {
      const blob = await downloadReportPdf(report, sources)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'informe_conciliacion_agent_conciliation.pdf'
      a.click()
      URL.revokeObjectURL(url)
    } catch (err: any) {
      setNotification({
        type: 'error',
        message: 'Error al generar el PDF: ' + err.message,
      })
    } finally {
      setDownloadingPdf(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors">
      <Header
        health={health}
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        onRunSamples={handleRunSamples}
        loadingSamples={loadingSamples}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 mb-6 border-b border-slate-200 dark:border-slate-800 pb-2">
          <button
            onClick={() => setActiveTab('reconciliation')}
            className={`flex items-center gap-2 px-4 py-2 text-xs font-bold rounded-xl transition-all cursor-pointer ${
              activeTab === 'reconciliation'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800'
            }`}
          >
            <LayoutDashboard className="h-4 w-4" />
            <span>Conciliación Financiera</span>
          </button>

          <button
            onClick={() => setActiveTab('copilot')}
            className={`flex items-center gap-2 px-4 py-2 text-xs font-bold rounded-xl transition-all cursor-pointer ${
              activeTab === 'copilot'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800'
            }`}
          >
            <MessageSquareCode className="h-4 w-4" />
            <span>Copilot Studio & Chat</span>
          </button>
        </div>

        {/* Global Notification Banner */}
        {notification && (
          <div
            className={`mb-6 p-4 rounded-xl text-xs font-medium flex items-center justify-between border ${
              notification.type === 'success'
                ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800'
                : 'bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-300 border-rose-200 dark:border-rose-800'
            }`}
          >
            <div className="flex items-center gap-2">
              {notification.type === 'success' ? (
                <FileCheck className="h-4 w-4 text-emerald-600" />
              ) : (
                <AlertCircle className="h-4 w-4 text-rose-600" />
              )}
              <span>{notification.message}</span>
            </div>
            <button
              onClick={() => setNotification(null)}
              className="text-slate-400 hover:text-slate-600 text-xs font-bold"
            >
              ×
            </button>
          </div>
        )}

        {/* View 1: Reconciliation Dashboard */}
        {activeTab === 'reconciliation' && (
          <div className="space-y-6">
            {/* Upload Zone */}
            <Dropzone
              onReconcile={handleUploadReconcile}
              loading={loadingReconcile}
            />

            {/* KPI Summary Cards */}
            {report && (
              <>
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Resultados del Cruce Contable
                  </h3>
                  {sources.length > 0 && (
                    <span className="text-[11px] text-slate-400 truncate max-w-md">
                      {sources.join(' · ')}
                    </span>
                  )}
                </div>

                <MetricCards
                  summary={report.summary}
                  activeCategory={activeCategory}
                  onSelectCategory={setActiveCategory}
                />

                <AuditTable
                  report={report}
                  activeCategory={activeCategory}
                  onSelectCategory={setActiveCategory}
                  onInspectItem={(item, category) => setInspectedItem({ item, category })}
                  onDownloadPdf={handleDownloadPdf}
                  downloadingPdf={downloadingPdf}
                />
              </>
            )}

            {!report && (
              <div className="text-center py-16 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-2xl p-6">
                <ShieldCheck className="h-10 w-10 text-slate-300 dark:text-slate-700 mx-auto mb-3" />
                <h4 className="text-sm font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Aún no se ha ejecutado ninguna conciliación
                </h4>
                <p className="text-xs text-slate-400 max-w-md mx-auto mb-4">
                  Carga los 3 reportes contables arriba o haz clic en «Probar con Muestras» en la barra superior para explorar la plataforma con datos sintéticos.
                </p>
              </div>
            )}
          </div>
        )}

        {/* View 2: Copilot Assistant Studio */}
        {activeTab === 'copilot' && (
          <CopilotChat health={health} />
        )}
      </main>

      {/* Drawer for Transaction Details */}
      <AuditDrawer
        item={inspectedItem?.item || null}
        category={inspectedItem?.category || ''}
        onClose={() => setInspectedItem(null)}
      />
    </div>
  )
}
export default App
