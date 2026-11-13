import { Landmark, ShieldCheck, Sun, Moon, Sparkles, RefreshCw } from 'lucide-react'
import type { SystemHealth } from '../types/reconciliation'

interface HeaderProps {
  health: SystemHealth | null
  darkMode: boolean
  setDarkMode: (val: boolean) => void
  onRunSamples: () => void
  loadingSamples: boolean
}

export const Header: React.FC<HeaderProps> = ({
  health,
  darkMode,
  setDarkMode,
  onRunSamples,
  loadingSamples,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand identity */}
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
            <Landmark className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight text-slate-900 dark:text-white">
                Agent Conciliation
              </span>
              <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded-full bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 border border-blue-200/60 dark:border-blue-800/60">
                FinTech 2.0
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
              Auditoría y Conciliación Multifuente con IA
            </p>
          </div>
        </div>

        {/* Status badges & Actions */}
        <div className="flex items-center gap-3">
          {/* Health indicator */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
            <span
              className={`h-2 w-2 rounded-full ${
                health?.status === 'healthy' ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
              }`}
            />
            <span>{health?.status === 'healthy' ? 'API Conectada' : 'Conectando...'}</span>
            {health?.copilot_authenticated && (
              <span className="flex items-center gap-1 text-blue-600 dark:text-blue-400 pl-1 border-l border-slate-300 dark:border-slate-600">
                <ShieldCheck className="h-3.5 w-3.5" />
                Copilot OK
              </span>
            )}
          </div>

          {/* Quick sample button */}
          <button
            onClick={onRunSamples}
            disabled={loadingSamples}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 active:scale-95 transition-all shadow-sm shadow-blue-600/30 disabled:opacity-50 cursor-pointer"
            title="Ejecuta la conciliación con los fixtures sintéticos del repositorio"
          >
            {loadingSamples ? (
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Sparkles className="h-3.5 w-3.5" />
            )}
            <span>Probar con Muestras</span>
          </button>

          {/* Theme switcher */}
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
            aria-label="Cambiar tema"
          >
            {darkMode ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4" />}
          </button>
        </div>
      </div>
    </header>
  )
}

