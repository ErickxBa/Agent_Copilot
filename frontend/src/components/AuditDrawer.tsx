import { useState } from 'react'
import { X, Copy, Check, FileText, Code } from 'lucide-react'
import type { ReconciliationItem } from '../types/reconciliation'

interface AuditDrawerProps {
  item: ReconciliationItem | null
  category: string
  onClose: () => void
}

export const AuditDrawer: React.FC<AuditDrawerProps> = ({ item, category, onClose }) => {
  const [copied, setCopied] = useState(false)

  if (!item) return null

  const isAlert = category === 'compliance_alerts'
  const jsonString = JSON.stringify(item.details || item, null, 2)

  const copyToClipboard = () => {
    navigator.clipboard.writeText(jsonString)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/50 backdrop-blur-xs flex justify-end transition-opacity">
      <div className="w-full max-w-xl bg-white dark:bg-slate-900 h-full shadow-2xl border-l border-slate-200 dark:border-slate-800 flex flex-col justify-between animate-in slide-in-from-right duration-300">
        {/* Drawer Header */}
        <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span
                className={`px-2 py-0.5 text-[11px] font-bold rounded-full uppercase tracking-wider ${
                  isAlert
                    ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-400 border border-rose-300 dark:border-rose-800'
                    : 'bg-blue-100 text-blue-700 dark:bg-blue-950/60 dark:text-blue-400 border border-blue-300 dark:border-blue-800'
                }`}
              >
                {isAlert ? 'Alerta AML / Cumplimiento' : 'Expediente de Auditoría'}
              </span>
              {item.payout_id && (
                <span className="text-xs font-mono font-semibold text-slate-500">
                  Payout #{item.payout_id}
                </span>
              )}
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              {isAlert ? `Regla: ${item.rule_id || 'AML Rule'}` : item.status || 'Excepción Detectada'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Drawer Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Reason / Description */}
          <div className="bg-slate-50 dark:bg-slate-800/60 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
            <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
              {isAlert ? 'Diagnóstico de Cumplimiento' : 'Motivo y Hallazgo'}
            </h4>
            <p className="text-sm text-slate-800 dark:text-slate-200 leading-relaxed font-medium">
              {isAlert ? item.description : item.reason}
            </p>
          </div>

          {/* Record IDs involved */}
          <div>
            <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
              Registros de Origen Involucrados
            </h4>
            <div className="flex flex-wrap gap-2">
              {item.record_ids?.map((id, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-1 text-xs font-mono font-medium rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 flex items-center gap-1.5"
                >
                  <FileText className="h-3 w-3 text-slate-400" />
                  {id}
                </span>
              ))}
            </div>
          </div>

          {/* Details / JSON Viewer */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Code className="h-4 w-4" />
                Evidencia Contable y Metadatos (JSON)
              </h4>
              <button
                onClick={copyToClipboard}
                className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 hover:underline cursor-pointer"
              >
                {copied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
                <span>{copied ? 'Copiado' : 'Copiar'}</span>
              </button>
            </div>
            <pre className="p-4 rounded-xl bg-slate-950 text-slate-200 font-mono text-xs overflow-x-auto border border-slate-800 max-h-72 leading-relaxed">
              {jsonString}
            </pre>
          </div>
        </div>

        {/* Drawer Footer */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 flex items-center justify-between">
          <span className="text-[11px] text-slate-400">
            Requiere validación y firma por un analista financiero.
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-200 hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors cursor-pointer"
          >
            Cerrar Ficha
          </button>
        </div>
      </div>
    </div>
  )
}
