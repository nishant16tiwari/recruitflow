import { Link } from 'react-router-dom'
import { useAlerts, useDismissAlert } from '@/api/alerts'
import { StageBadge } from '@/components/StageBadge'
import { useToast } from '@/components/Toast'
import { getErrorMessage } from '@/lib/api'

export function AlertsPage() {
  const { data, isLoading } = useAlerts(true)
  const dismiss = useDismissAlert()
  const { showToast } = useToast()

  function handleDismiss(applicationId: number, name: string) {
    dismiss.mutate(applicationId, {
      onSuccess: () => showToast(`Alert dismissed for ${name}`),
      onError: (err) => showToast(getErrorMessage(err), 'error'),
    })
  }

  return (
    <div className="p-8 max-w-4xl">
      <h1 className="font-serif text-2xl text-ink mb-1">Alerts</h1>
      <p className="text-sm text-ink-soft mb-8">
        Candidates who have sat in the same stage for more than 10 days.
      </p>

      {isLoading && <p className="text-sm text-ink-soft">Loading...</p>}

      {!isLoading && data?.alerts.length === 0 && (
        <div className="border border-line rounded-md px-6 py-10 text-center">
          <p className="text-sm text-ink-soft">No stalled candidates right now. Nice work keeping things moving.</p>
        </div>
      )}

      <ul className="flex flex-col gap-3">
        {data?.alerts.map((alert) => (
          <li
            key={alert.application_id}
            className="flex items-center justify-between border border-line rounded-md px-4 py-3"
          >
            <div>
              <Link
                to={`/applications/${alert.application_id}`}
                className="text-sm font-medium text-ink hover:text-pine"
              >
                {alert.candidate_name}
              </Link>
              <p className="text-xs text-ink-soft mt-0.5">{alert.job_title}</p>
            </div>
            <div className="flex items-center gap-4">
              <StageBadge stage={alert.current_stage} />
              <span className="text-sm text-amber font-medium w-24 text-right">
                {alert.days_in_stage} days in stage
              </span>
              <button
                onClick={() => handleDismiss(alert.application_id, alert.candidate_name)}
                disabled={dismiss.isPending}
                className="text-sm border border-line rounded-md px-3 py-1.5 text-ink-soft hover:text-ink disabled:opacity-60"
              >
                Dismiss
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
