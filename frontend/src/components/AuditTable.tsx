import { useState, useMemo } from 'react'
import {
  Search,
  Eye,
  FileDown,
  Layers,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  ShieldAlert,
  Percent,
} from 'lucide-react'
import type { ReconciliationReport, ReconciliationItem } from '../types/reconciliation'

interface AuditTableProps {
  report: ReconciliationReport | null
  activeCategory: string
  onSelectCategory: (category: string) => void
  onInspectItem: (item: ReconciliationItem, category: string) => void
  onDownloadPdf: () => void
  downloadingPdf: boolean
}

export const AuditTable: React.FC<AuditTableProps> = ({
  report,
  activeCategory,
  onSelectCategory,
  onInspectItem,
  onDownloadPdf,
  downloadingPdf,
}) => {
  const [searchQuery, setSearchQuery] = useState('')

  if (!report) return null

  // Map of categories and items
  const categoryConfig: Record<string, { label: string; items: ReconciliationItem[]; icon: any; color: string }> = {
    exact_matches: {
      label: 'Coincidencias Exactas',
      items: report.exact_matches || [],
      icon: CheckCircle2,
      color: 'text-emerald-500',
    },
    fuzzy_fee_matches: {
      label: 'Tarifas (Fuzzy)',
      items: report.fuzzy_fee_matches || [],
      icon: Percent,
      color: 'text-sky-500',
    },
    reconciliation_exceptions: {
      label: 'Excepciones',
      items: report.reconciliation_exceptions || [],
      icon: AlertTriangle,
      color: 'text-amber-500',
    },
    orphan_transactions: {
      label: 'Huérfanas',
      items: report.orphan_transactions || [],
      icon: HelpCircle,
      color: 'text-orange-500',
    },
    compliance_alerts: {
      label: 'Alertas AML',
      items: report.compliance_alerts || [],
      icon: ShieldAlert,
      color: 'text-rose-500',
    },
  }

  // Current items based on activeCategory
  const currentCategoryData = categoryConfig[activeCategory] || categoryConfig['exact_matches']
  const items = currentCategoryData.items

  // Filter items by search query
  const filteredItems = useMemo(() => {
    if (!searchQuery.trim()) return items
    const q = searchQuery.toLowerCase()
    return items.filter((item) => {
      const payoutStr = String(item.payout_id || '').toLowerCase()
      const reasonStr = (item.reason || item.description || '').toLowerCase()
      const recordsStr = (item.record_ids || []).join(' ').toLowerCase()
      const ruleStr = (item.rule_id || '').toLowerCase()
      return (
        payoutStr.includes(q) ||
        reasonStr.includes(q) ||
        recordsStr.includes(q) ||
        ruleStr.includes(q)
      )
    })
  }, [items, searchQuery])

  const downloadJson = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'conciliacion_financiera_audit.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden my-6">
      {/* Table Top Toolbar */}
      <div className="p-4 sm:p-6 border-b border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Layers className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            Matriz de Auditoría y Discrepancias
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {filteredItems.length} registros en categoría «{currentCategoryData.label}»
          </p>
        </div>

        {/* Actions: Export PDF & JSON */}
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <button
            onClick={onDownloadPdf}
            disabled={downloadingPdf}
            className="flex-1 sm:flex-none flex items-center justify-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-xl transition-all shadow-sm shadow-blue-500/20 disabled:opacity-50 cursor-pointer"
          >
            <FileDown className="h-4 w-4" />
            <span>{downloadingPdf ? 'Generando PDF...' : 'Descargar Informe (PDF)'}</span>
          </button>
          <button
            onClick={downloadJson}
            className="flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-700 dark:text-slate-300 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 rounded-xl transition-colors cursor-pointer"
          >
            <span>JSON</span>
          </button>
        </div>
      </div>

      {/* Tabs for Category selection */}
      <div className="flex overflow-x-auto border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/20 px-4 scrollbar-none">
        {Object.entries(categoryConfig).map(([key, config]) => {
          const Icon = config.icon
          const isSelected = activeCategory === key
          const count = config.items.length
          return (
            <button
              key={key}
              onClick={() => onSelectCategory(key)}
              className={`flex items-center gap-2 py-3 px-4 text-xs font-semibold border-b-2 transition-all whitespace-nowrap cursor-pointer ${
                isSelected
                  ? 'border-blue-600 text-blue-600 dark:text-blue-400 bg-white dark:bg-slate-900 shadow-xs'
                  : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
              }`}
            >
              <Icon className={`h-3.5 w-3.5 ${config.color}`} />
              <span>{config.label}</span>
              <span
                className={`px-1.5 py-0.5 rounded-full text-[10px] tabular-nums ${
                  isSelected
                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/60 dark:text-blue-300'
                    : 'bg-slate-200/70 dark:bg-slate-700 text-slate-600 dark:text-slate-400'
                }`}
              >
                {count}
              </span>
            </button>
          )
        })}
      </div>

      {/* Search Input Bar */}
      <div className="p-4 bg-white dark:bg-slate-900 border-b border-slate-100 dark:border-slate-800 flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Buscar por Payout ID, código de registro, regla o motivo..."
            className="w-full pl-9 pr-4 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
          />
        </div>
      </div>

      {/* Table Records */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800 font-semibold uppercase tracking-wider text-[10px]">
            <tr>
              <th className="py-3 px-4">#</th>
              <th className="py-3 px-4">Payout ID / Regla</th>
              <th className="py-3 px-4">Registros de Origen</th>
              <th className="py-3 px-4">Estado / Diagnóstico</th>
              <th className="py-3 px-4">Motivo / Causa</th>
              <th className="py-3 px-4 text-right">Acción</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-medium text-slate-700 dark:text-slate-300">
            {filteredItems.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-slate-400">
                  No se encontraron elementos en esta categoría con el filtro actual.
                </td>
              </tr>
            ) : (
              filteredItems.map((item, index) => {
                const isAlert = activeCategory === 'compliance_alerts'
                return (
                  <tr
                    key={index}
                    onClick={() => onInspectItem(item, activeCategory)}
                    className="hover:bg-blue-50/40 dark:hover:bg-slate-800/40 transition-colors cursor-pointer group"
                  >
                    <td className="py-3.5 px-4 font-mono text-slate-400 text-[11px] tabular-nums">
                      {index + 1}
                    </td>
                    <td className="py-3.5 px-4 font-mono font-semibold text-slate-900 dark:text-white">
                      {isAlert ? (
                        <span className="px-2 py-0.5 rounded-md bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-400 font-bold">
                          {item.rule_id}
                        </span>
                      ) : (
                        item.payout_id || <span className="text-slate-400 italic">No especificado</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex flex-wrap gap-1">
                        {item.record_ids?.map((rid, rIdx) => (
                          <span
                            key={rIdx}
                            className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-[10px] font-mono text-slate-600 dark:text-slate-400"
                          >
                            {rid}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          isAlert
                            ? 'bg-rose-100 dark:bg-rose-900/40 text-rose-700 dark:text-rose-300'
                            : 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300'
                        }`}
                      >
                        {isAlert ? `Severidad ${item.severity || 'Media'}` : item.status || 'OK'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 max-w-xs truncate text-slate-600 dark:text-slate-400">
                      {isAlert ? item.description : item.reason}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          onInspectItem(item, activeCategory)
                        }}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/60 transition-colors cursor-pointer"
                      >
                        <Eye className="h-3.5 w-3.5" />
                        <span>Ver Ficha</span>
                      </button>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
