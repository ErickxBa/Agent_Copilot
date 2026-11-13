import { useState, useRef } from 'react'
import { UploadCloud, FileText, CheckCircle2, ArrowRight, Shield } from 'lucide-react'

interface DropzoneProps {
  onReconcile: (bank: File, gateway: File, ledger: File) => void
  loading: boolean
}

export const Dropzone: React.FC<DropzoneProps> = ({ onReconcile, loading }) => {
  const [bankFile, setBankFile] = useState<File | null>(null)
  const [gatewayFile, setGatewayFile] = useState<File | null>(null)
  const [ledgerFile, setLedgerFile] = useState<File | null>(null)
  const [consent, setConsent] = useState(true)

  const bankInputRef = useRef<HTMLInputElement>(null)
  const gatewayInputRef = useRef<HTMLInputElement>(null)
  const ledgerInputRef = useRef<HTMLInputElement>(null)

  const readyCount = (bankFile ? 1 : 0) + (gatewayFile ? 1 : 0) + (ledgerFile ? 1 : 0)
  const canSubmit = readyCount === 3 && consent && !loading

  const handleStart = () => {
    if (bankFile && gatewayFile && ledgerFile) {
      onReconcile(bankFile, gatewayFile, ledgerFile)
    }
  }

  const sources = [
    {
      id: 'bank',
      title: 'Reporte de Banco',
      subtitle: 'bank_id, payout_id, settled_at, amount',
      file: bankFile,
      setFile: setBankFile,
      ref: bankInputRef,
    },
    {
      id: 'gateway',
      title: 'Reporte de Pasarela',
      subtitle: 'gateway_id, gross_amount, transaction_at',
      file: gatewayFile,
      setFile: setGatewayFile,
      ref: gatewayInputRef,
    },
    {
      id: 'ledger',
      title: 'Reporte de Libro Mayor',
      subtitle: 'ledger_id, amount, posted_at, currency',
      file: ledgerFile,
      setFile: setLedgerFile,
      ref: ledgerInputRef,
    },
  ]

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm my-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800 gap-2">
        <div>
          <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <UploadCloud className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            Ingesta de Fuentes Contables
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Sube los tres extractos sintéticos (formato JSON o TXT estructurado) para iniciar el cruce.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
          <span>{readyCount} de 3 fuentes listas</span>
          {readyCount === 3 ? (
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          ) : (
            <span className="h-2 w-2 rounded-full bg-amber-400" />
          )}
        </div>
      </div>

      {/* Grid of 3 upload cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 my-5">
        {sources.map((src) => (
          <div
            key={src.id}
            onClick={() => src.ref.current?.click()}
            className={`relative p-4 rounded-xl border-2 border-dashed transition-all cursor-pointer flex flex-col justify-between min-h-[140px] ${
              src.file
                ? 'border-emerald-400 bg-emerald-50/30 dark:bg-emerald-950/20 dark:border-emerald-700'
                : 'border-slate-200 hover:border-blue-400 dark:border-slate-700 dark:hover:border-blue-500 bg-slate-50/50 dark:bg-slate-800/40'
            }`}
          >
            <input
              type="file"
              ref={src.ref}
              className="hidden"
              accept=".json,.txt"
              onChange={(e) => {
                if (e.target.files?.[0]) src.setFile(e.target.files[0])
              }}
            />
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <div
                  className={`p-2 rounded-lg ${
                    src.file
                      ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/60 dark:text-emerald-300'
                      : 'bg-slate-200/70 text-slate-600 dark:bg-slate-700 dark:text-slate-300'
                  }`}
                >
                  <FileText className="h-4 w-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">
                    {src.title}
                  </h4>
                  <p className="text-[10px] text-slate-400">{src.subtitle}</p>
                </div>
              </div>
              {src.file && (
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
              )}
            </div>

            <div className="mt-3 pt-2 border-t border-slate-200/60 dark:border-slate-700/60 text-xs">
              {src.file ? (
                <div className="flex items-center justify-between text-emerald-700 dark:text-emerald-400 font-medium">
                  <span className="truncate max-w-[170px]">{src.file.name}</span>
                  <span className="text-[10px] tabular-nums">
                    {(src.file.size / 1024).toFixed(1)} KB
                  </span>
                </div>
              ) : (
                <span className="text-slate-400 text-[11px]">
                  Haz clic o arrastra el archivo aquí
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Footer controls: Consent & Submit */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs">
        <label className="flex items-center gap-2 cursor-pointer select-none text-slate-600 dark:text-slate-300">
          <input
            type="checkbox"
            checked={consent}
            onChange={(e) => setConsent(e.target.checked)}
            className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
          />
          <span className="flex items-center gap-1.5 font-medium">
            <Shield className="h-3.5 w-3.5 text-blue-500" />
            Confirmo que los archivos contienen datos sintéticos de prueba.
          </span>
        </label>

        <button
          onClick={handleStart}
          disabled={!canSubmit}
          className={`flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs text-white transition-all shadow-sm ${
            canSubmit
              ? 'bg-blue-600 hover:bg-blue-700 active:scale-95 shadow-blue-500/30 cursor-pointer'
              : 'bg-slate-300 dark:bg-slate-800 text-slate-400 dark:text-slate-600 cursor-not-allowed'
          }`}
        >
          <span>{loading ? 'Validando y Conciliando...' : 'Iniciar Conciliación'}</span>
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
