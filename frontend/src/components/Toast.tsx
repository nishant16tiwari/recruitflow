import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'
import { CheckCircle2, XCircle, X } from 'lucide-react'

interface Toast {
  id: number
  message: string
  variant: 'success' | 'error'
}

interface ToastContextValue {
  showToast: (message: string, variant?: 'success' | 'error') => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const showToast = useCallback((message: unknown, variant: 'success' | 'error' = 'success') => {
    const id = Date.now() + Math.random()
    const strMessage = typeof message === 'string' ? message : JSON.stringify(message)
    setToasts((prev) => [...prev, { id, message: strMessage, variant }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 4000)
  }, [])

  const dismiss = (id: number) => setToasts((prev) => prev.filter((t) => t.id !== id))

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 w-full max-w-sm">
        {toasts.map((t) => (
          <div
            key={t.id}
            role="status"
            className={`flex items-start gap-3 rounded-md border px-4 py-3 shadow-sm bg-surface ${
              t.variant === 'success' ? 'border-pine/30' : 'border-rose/30'
            }`}
          >
            {t.variant === 'success' ? (
              <CheckCircle2 size={18} className="text-pine mt-0.5 shrink-0" />
            ) : (
              <XCircle size={18} className="text-rose mt-0.5 shrink-0" />
            )}
            <p className="text-sm text-ink flex-1">{String(t.message)}</p>
            <button
              onClick={() => dismiss(t.id)}
              aria-label="Dismiss notification"
              className="text-ink-soft hover:text-ink"
            >
              <X size={16} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
