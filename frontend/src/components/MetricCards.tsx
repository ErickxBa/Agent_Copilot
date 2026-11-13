import { CheckCircle2, Percent, AlertTriangle, HelpCircle, ShieldAlert } from 'lucide-react'
import type { SummaryCounts } from '../types/reconciliation'

interface MetricCardsProps {
  summary: SummaryCounts | null
  activeCategory: string
  onSelectCategory: (category: string) => void
}

export const MetricCards: React.FC<MetricCardsProps> = ({
  summary,
  activeCategory,
  onSelectCategory,
}) => {
  if (!summary) return null

  const cards = [
    {
      id: 'exact_matches',
      label: 'Coincidencias Exactas',
      count: summary.exact_matches || 0,
      description: 'Monto, fecha y payout ID determinista',
      icon: CheckCircle2,
      color: 'text-emerald-600 dark:text-emerald-400',
      bg: 'bg-emerald-50 dark:bg-emerald-950/40',
      border: 'border-emerald-200 dark:border-emerald-800/60',
      activeBorder: 'ring-2 ring-emerald-500',
    },
    {
      id: 'fuzzy_fee_matches',
      label: 'Regla de Tarifas',
      count: summary.fuzzy_fee_matches || 0,
      description: 'Comisión de pasarela y ventana 48h',
      icon: Percent,
      color: 'text-sky-600 dark:text-sky-400',
      bg: 'bg-sky-50 dark:bg-sky-950/40',
      border: 'border-sky-200 dark:border-sky-800/60',
      activeBorder: 'ring-2 ring-sky-500',
    },
    {
      id: 'reconciliation_exceptions',
      label: 'Excepciones Contables',
      count: summary.reconciliation_exceptions || 0,
      description: 'Diferencias auditadas por el modelo IA',
      icon: AlertTriangle,
      color: 'text-amber-600 dark:text-amber-400',
      bg: 'bg-amber-50 dark:bg-amber-950/40',
      border: 'border-amber-200 dark:border-amber-800/60',
      activeBorder: 'ring-2 ring-amber-500',
    },
    {
      id: 'orphan_transactions',
      label: 'Transacciones Huérfanas',
      count: summary.orphan_transactions || 0,
      description: 'Sin contraparte en lotes de liquidación',
      icon: HelpCircle,
      color: 'text-orange-600 dark:text-orange-400',
      bg: 'bg-orange-50 dark:bg-orange-950/40',
      border: 'border-orange-200 dark:border-orange-800/60',
      activeBorder: 'ring-2 ring-orange-500',
    },
    {
      id: 'compliance_alerts',
      label: 'Alertas AML / Riesgo',
      count: summary.compliance_alerts || 0,
      description: 'Monitoreo de umbral y patrones sospechosos',
      icon: ShieldAlert,
      color: 'text-rose-600 dark:text-rose-400',
      bg: 'bg-rose-50 dark:bg-rose-950/40',
      border: 'border-rose-200 dark:border-rose-800/60',
      activeBorder: 'ring-2 ring-rose-500',
    },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5 my-6">
      {cards.map((card) => {
        const Icon = card.icon
        const isSelected = activeCategory === card.id
        return (
          <button
            key={card.id}
            onClick={() => onSelectCategory(card.id)}
            className={`flex flex-col text-left p-4 rounded-xl border transition-all duration-200 cursor-pointer ${
              card.border
            } ${card.bg} ${
              isSelected ? `${card.activeBorder} shadow-md scale-[1.02]` : 'hover:shadow-sm opacity-90 hover:opacity-100'
            }`}
          >
            <div className="flex items-center justify-between w-full mb-2">
              <span className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                {card.label}
              </span>
              <Icon className={`h-4 w-4 ${card.color}`} />
            </div>
            <div className={`text-2xl font-bold tracking-tight tabular-nums ${card.color}`}>
              {card.count}
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 leading-snug line-clamp-2">
              {card.description}
            </p>
          </button>
        )
      })}
    </div>
  )
}

