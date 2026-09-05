import { CheckCircle2, XCircle, X } from 'lucide-react'
import type { BulkActionResult } from '@/lib/types'

export function BulkResultsPanel({ results, onDismiss }: { results: BulkActionResult[]; onDismiss: () => void }) {
  const successCount = results.filter((r) => r.success).length
  const failCount = results.length - successCount

  return (
    <div className="border border-line rounded-md mb-4 bg-surface">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-line">
        <p className="text-sm text-ink">
          <span className="font-medium">{successCount} succeeded</span>
          {failCount > 0 && <span className="text-rose">, {failCount} failed</span>}
        </p>
        <button onClick={onDismiss} aria-label="Dismiss results" className="text-ink-soft hover:text-ink">
          <X size={16} />
        </button>
      </div>
      <ul className="max-h-48 overflow-y-auto divide-y divide-line-soft">
        {results.map((r) => (
          <li key={r.application_id} className="flex items-start gap-2.5 px-4 py-2 text-sm">
            {r.success ? (
              <CheckCircle2 size={16} className="text-pine mt-0.5 shrink-0" />
            ) : (
              <XCircle size={16} className="text-rose mt-0.5 shrink-0" />
            )}
            <span className="text-ink-soft">
              Application #{r.application_id}
              {r.success ? (
                <span className="text-ink">
                  {' '}
                  moved {r.old_stage} → {r.new_stage}
                </span>
              ) : (
                <span className="text-rose"> — {r.reason}</span>
              )}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
