import { useState, useEffect, useRef } from 'react'
import {
  Send,
  Paperclip,
  Bot,
  User,
  ToggleLeft,
  ToggleRight,
  PlusCircle,
  FileText,
  AlertCircle,
  ShieldCheck,
} from 'lucide-react'
import type {
  CopilotSession,
  ChatMessage,
  SystemHealth,
} from '../types/reconciliation'
import {
  listCopilotSessions,
  createCopilotSession,
  sendChatMessage,
  fetchCopilotAuth,
} from '../services/api'

const SKILL_OPTIONS = [
  {
    id: 'reconciliation-engineering',
    label: 'Conciliación & Auditoría',
    description: 'Reglas financieras PoC',
  },
  {
    id: 'source-format-validation',
    label: 'Fuentes y formatos',
    description: 'Validación sin asumir formatos oficiales',
  },
  {
    id: 'exception-evidence-analysis',
    label: 'Excepciones y evidencia',
    description: 'Hallazgos sustentados en registros de origen',
  },
  {
    id: 'audit-reporting',
    label: 'Reportes y trazabilidad',
    description: 'Evidencia verificable para revisión analista',
  },
] as const

interface CopilotChatProps {
  health: SystemHealth | null
}

export const CopilotChat: React.FC<CopilotChatProps> = ({ health }) => {
  const [sessions, setSessions] = useState<CopilotSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [attachment, setAttachment] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [authStatus, setAuthStatus] = useState<{ is_authenticated: boolean; login: string | null } | null>(null)

  const [activeSkills, setActiveSkills] = useState<string[]>(
    () => SKILL_OPTIONS.map(({ id }) => id)
  )

  const fileInputRef = useRef<HTMLInputElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const checkAuth = async () => {
    try {
      const res = await fetchCopilotAuth()
      setAuthStatus(res)
    } catch {
      setAuthStatus({ is_authenticated: false, login: null })
    }
  }

  const toggleSkill = (skillId: string) => {
    setActiveSkills((currentSkills) =>
      currentSkills.includes(skillId)
        ? currentSkills.filter((id) => id !== skillId)
        : [...currentSkills, skillId]
    )
  }

  // Load sessions and auth
  useEffect(() => {
    checkAuth()
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      const data = await listCopilotSessions()
      setSessions(data)
      if (data.length > 0 && !currentSessionId) {
        setCurrentSessionId(data[0].session_id)
      }
    } catch (e: any) {
      console.warn('No active sessions:', e.message)
    }
  }

  const handleCreateSession = async () => {
    try {
      setLoading(true)
      const res = await createCopilotSession(
        `Agent Conciliation · ${new Date().toLocaleDateString()}`,
        activeSkills
      )
      setCurrentSessionId(res.session_id)
      setMessages([])
      await loadSessions()
    } catch (e: any) {
      setErrorMsg(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSendMessage = async (text?: string) => {
    const msgToSend = text || inputValue
    if (!msgToSend.trim() && !attachment) return

    let sessionId = currentSessionId
    if (!sessionId) {
      try {
        const res = await createCopilotSession('Nueva Conversación', activeSkills)
        sessionId = res.session_id
        setCurrentSessionId(sessionId)
      } catch (e: any) {
        setErrorMsg('Error creando sesión: ' + e.message)
        return
      }
    }

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: msgToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      attachmentName: attachment?.name,
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue('')
    const attachedFile = attachment
    setAttachment(null)
    setLoading(true)
    setErrorMsg(null)

    try {
      const resp = await sendChatMessage(
        sessionId,
        msgToSend,
        activeSkills,
        attachedFile || undefined
      )
      const botMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: resp.assistant_content,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      setMessages((prev) => [...prev, botMessage])
    } catch (e: any) {
      setErrorMsg(e.message || 'Error comunicando con Copilot')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const promptSuggestions = [
    '¿Qué formato deben tener los tres reportes?',
    '¿Cómo funciona la regla de comisión 48h?',
    'Explica las alertas AML implementadas',
    '¿Qué diferencia hay entre una excepción y una transacción huérfana?',
  ]

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden my-6 flex flex-col md:flex-row h-[650px]">
      {/* Sidebar: Skills & Sessions */}
      <div className="w-full md:w-72 border-r border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-950/40 p-4 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Copilot Studio
            </h4>
            <button
              onClick={handleCreateSession}
              disabled={loading}
              className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 font-semibold hover:underline cursor-pointer"
            >
              <PlusCircle className="h-3.5 w-3.5" />
              <span>Nueva</span>
            </button>
          </div>

          {/* Session Selector */}
          <div className="mb-5">
            <label className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 mb-1 block">
              Sesión Activa
            </label>
            <select
              value={currentSessionId || ''}
              onChange={(e) => {
                setCurrentSessionId(e.target.value)
                setMessages([])
              }}
              className="w-full p-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
            >
              {sessions.map((s) => (
                <option key={s.session_id} value={s.session_id}>
                  {s.summary?.slice(0, 30) || 'Conversación'} ({s.modified_time.slice(0, 10)})
                </option>
              ))}
              {sessions.length === 0 && <option value="">Sin sesiones previas</option>}
            </select>
          </div>

          {/* Skills Controls */}
          <div className="space-y-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <h5 className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Skills Habilitadas
            </h5>

            {SKILL_OPTIONS.map(({ id, label, description }) => {
              const isEnabled = activeSkills.includes(id)
              return (
                <button
                  key={id}
                  type="button"
                  aria-pressed={isEnabled}
                  onClick={() => toggleSkill(id)}
                  className="flex w-full items-center justify-between p-2.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 cursor-pointer text-left text-xs"
                >
                  <span>
                    <span className="font-semibold block text-slate-800 dark:text-slate-200">
                      {label}
                    </span>
                    <span className="text-[10px] text-slate-400">{description}</span>
                  </span>
                  {isEnabled ? (
                    <ToggleRight className="h-5 w-5 text-blue-600" />
                  ) : (
                    <ToggleLeft className="h-5 w-5 text-slate-400" />
                  )}
                </button>
              )
            })}
          </div>
        </div>

        {/* Security Notice */}
        <div className="p-3 rounded-xl bg-blue-50/60 dark:bg-blue-950/30 border border-blue-200/60 dark:border-blue-900/40 text-[11px] text-slate-600 dark:text-slate-400">
          <ShieldCheck className="h-4 w-4 text-blue-500 mb-1" />
          <span>
            {health?.copilot_authenticated ? 'Copilot SDK CLI Conectado' : 'Modo PoC Seguro'}: Usa exclusivamente datos sintéticos.
          </span>
        </div>
      </div>

      {/* Main Chat Stream */}
      <div className="flex-1 flex flex-col justify-between bg-white dark:bg-slate-900">
        {/* Auth notice banner */}
        {authStatus && !authStatus.is_authenticated && (
          <div className="mx-4 mt-4 p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-xs text-amber-800 dark:text-amber-300 flex items-start justify-between gap-3 shadow-xs">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-[11px]">Copilot CLI no autenticado</p>
                <p className="text-[11px] text-amber-700 dark:text-amber-400 mt-0.5">
                  Para habilitar respuestas en vivo, ejecuta <code className="px-1 py-0.5 rounded bg-amber-200/60 dark:bg-amber-900 font-mono text-[10px]">copilot</code> o <code className="px-1 py-0.5 rounded bg-amber-200/60 dark:bg-amber-900 font-mono text-[10px]">gh auth login</code> en una terminal.
                </p>
              </div>
            </div>
            <button
              onClick={checkAuth}
              className="px-2.5 py-1 text-[11px] font-semibold rounded-lg bg-amber-200/80 dark:bg-amber-800 hover:bg-amber-300 dark:hover:bg-amber-700 transition-colors shrink-0 cursor-pointer"
            >
              Comprobar
            </button>
          </div>
        )}

        {/* Messages list */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400">
              <div className="h-12 w-12 rounded-2xl bg-blue-50 dark:bg-blue-950/60 flex items-center justify-center text-blue-600 dark:text-blue-400 mb-3 shadow-xs">
                <Bot className="h-6 w-6" />
              </div>
              <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200 mb-1">
                ¿En qué puedo asistirte hoy?
              </h4>
              <p className="text-xs max-w-sm mb-6 text-slate-500">
                Formula preguntas sobre la conciliación contable, o adjunta un archivo para auditarlo.
              </p>

              {/* Suggestions */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-md w-full text-left">
                {promptSuggestions.map((sug, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(sug)}
                    className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-blue-400 dark:hover:border-blue-600 text-xs text-slate-600 dark:text-slate-300 hover:bg-blue-50/50 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                  >
                    {sug}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m) => (
              <div
                key={m.id}
                className={`flex gap-3 text-xs leading-relaxed ${
                  m.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {m.role === 'assistant' && (
                  <div className="h-7 w-7 rounded-lg bg-blue-600 flex items-center justify-center text-white shrink-0 mt-0.5">
                    <Bot className="h-4 w-4" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-2xl p-4 ${
                    m.role === 'user'
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700 whitespace-pre-wrap'
                  }`}
                >
                  {m.attachmentName && (
                    <div className="flex items-center gap-1.5 mb-2 pb-2 border-b border-white/20 text-[11px] font-semibold">
                      <FileText className="h-3.5 w-3.5" />
                      <span>Adjunto: {m.attachmentName}</span>
                    </div>
                  )}
                  <div>{m.content}</div>
                  <span
                    className={`block text-[10px] mt-2 text-right ${
                      m.role === 'user' ? 'text-blue-200' : 'text-slate-400'
                    }`}
                  >
                    {m.timestamp}
                  </span>
                </div>
                {m.role === 'user' && (
                  <div className="h-7 w-7 rounded-lg bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-700 dark:text-slate-200 shrink-0 mt-0.5">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))
          )}

          {loading && (
            <div className="flex gap-3 text-xs justify-start">
              <div className="h-7 w-7 rounded-lg bg-blue-600 flex items-center justify-center text-white shrink-0">
                <Bot className="h-4 w-4" />
              </div>
              <div className="p-3.5 rounded-2xl bg-slate-100 dark:bg-slate-800 text-slate-500 flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
                <span className="h-2 w-2 rounded-full bg-blue-500 animate-pulse delay-150" />
                <span className="h-2 w-2 rounded-full bg-blue-500 animate-pulse delay-300" />
                <span className="text-[11px]">Analizando contexto contable...</span>
              </div>
            </div>
          )}

          {errorMsg && (
            <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-xs text-rose-600 flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Composer */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          {attachment && (
            <div className="flex items-center justify-between mb-2 p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-xs">
              <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
                <FileText className="h-4 w-4 text-blue-500" />
                <span className="font-medium truncate max-w-xs">{attachment.name}</span>
              </div>
              <button
                onClick={() => setAttachment(null)}
                className="text-slate-400 hover:text-slate-600 text-xs font-bold"
              >
                ×
              </button>
            </div>
          )}

          <div className="flex items-center gap-2">
            <input
              type="file"
              ref={fileInputRef}
              className="hidden"
              accept=".json,.txt"
              onChange={(e) => {
                if (e.target.files?.[0]) setAttachment(e.target.files[0])
              }}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-500 hover:text-blue-600 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer"
              title="Adjuntar archivo JSON/TXT"
            >
              <Paperclip className="h-4 w-4" />
            </button>

            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Pregunta sobre las reglas de reconciliación o adjunta un extracto..."
              className="flex-1 py-2.5 px-4 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
            />

            <button
              onClick={() => handleSendMessage()}
              disabled={loading || (!inputValue.trim() && !attachment)}
              className="p-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 active:scale-95 text-white disabled:opacity-40 transition-all cursor-pointer shadow-sm shadow-blue-500/20"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
