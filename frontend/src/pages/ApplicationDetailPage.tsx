import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { useApplication, useAdvanceApplication, useRejectApplication, useReinstateApplication } from '@/api/applications'
import { useJob } from '@/api/jobs'
import { useHistory } from '@/api/history'
import { useCurrentUser } from '@/hooks/useAuth'
import { usePanel } from '@/api/panel'
import { PipelineStepper } from '@/components/PipelineStepper'
import { PanelSection } from '@/components/PanelSection'
import { FeedbackSection } from '@/components/FeedbackSection'
import { InterviewsSection } from '@/components/InterviewsSection'
import { Timeline } from '@/components/Timeline'
import { useToast } from '@/components/Toast'
import { getErrorMessage } from '@/lib/api'
import { format, parseISO } from 'date-fns'

export function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const applicationId = Number(id)
  const { showToast } = useToast()

  const { data: app, isLoading } = useApplication(applicationId)
  const { data: job } = useJob(app?.job_id)
  const { data: history } = useHistory(applicationId)
  const { data: user } = useCurrentUser()
  const { data: panel } = usePanel(applicationId)

  const advance = useAdvanceApplication()
  const reject = useRejectApplication()
  const reinstate = useReinstateApplication()

  const [showRejectConfirm, setShowRejectConfirm] = useState(false)

  const isRecruiter = user?.role === 'RECRUITER'
  const isAssignedInterviewer =
    user?.role === 'INTERVIEWER' && !!panel?.some((p) => p.interviewer_id === user.id)

  if (isLoading || !app) {
    return (
      <div className="p-8">
        <p className="text-ink-soft text-sm">Loading...</p>
      </div>
    )
  }

  function handleAdvance() {
    advance.mutate(applicationId, {
      onSuccess: (updated) => showToast(`Moved to ${updated.current_stage}`),
      onError: (err) => showToast(getErrorMessage(err), 'error'),
    })
  }

  function handleReject() {
    reject.mutate(
      { id: applicationId },
      {
        onSuccess: () => {
          showToast('Application rejected')
          setShowRejectConfirm(false)
        },
        onError: (err) => showToast(getErrorMessage(err), 'error'),
      },
    )
  }

  function handleReinstate() {
    reinstate.mutate(applicationId, {
      onSuccess: (updated) => showToast(`Reinstated to ${updated.current_stage}`),
      onError: (err) => showToast(getErrorMessage(err), 'error'),
    })
  }

  const canAdvance = isRecruiter && app.current_stage !== 'Hired' && app.current_stage !== 'Rejected'
  const canReject = isRecruiter && app.current_stage !== 'Hired' && app.current_stage !== 'Rejected'
  const canReinstate = isRecruiter && app.current_stage === 'Rejected'

  return (
    <div className="p-8 max-w-4xl">
      <Link to="/applications" className="flex items-center gap-1.5 text-sm text-ink-soft hover:text-ink mb-6">
        <ArrowLeft size={15} /> Back to applications
      </Link>

      <div className="flex items-start justify-between mb-2">
        <div>
          <h1 className="font-serif text-2xl text-ink">{app.candidate_name}</h1>
          <p className="text-sm text-ink-soft mt-0.5">
            {app.candidate_email} · {job?.title ?? '—'}
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-ink-soft mb-8">
        <span>Source: {app.source}</span>
        <span>Applied {format(parseISO(app.applied_date), 'MMM d, yyyy')}</span>
      </div>

      <div className="border-y border-line py-6 mb-8 overflow-x-auto">
        <PipelineStepper
          currentStage={app.current_stage}
          previousStageBeforeRejection={app.previous_stage_before_rejection}
        />
      </div>

      {isRecruiter && (
        <div className="flex items-center gap-2 mb-8">
          {canAdvance && (
            <button
              onClick={handleAdvance}
              disabled={advance.isPending}
              className="text-sm bg-pine hover:bg-pine-deep text-white rounded-md px-3.5 py-2 disabled:opacity-60"
            >
              Advance to next stage
            </button>
          )}
          {canReject && (
            <button
              onClick={() => setShowRejectConfirm(true)}
              className="text-sm border border-rose/30 text-rose hover:bg-rose-soft rounded-md px-3.5 py-2"
            >
              Reject
            </button>
          )}
          {canReinstate && (
            <button
              onClick={handleReinstate}
              disabled={reinstate.isPending}
              className="text-sm bg-pine hover:bg-pine-deep text-white rounded-md px-3.5 py-2 disabled:opacity-60"
            >
              Reinstate to {app.previous_stage_before_rejection}
            </button>
          )}
        </div>
      )}

      {app.notes && (
        <div className="mb-8">
          <h2 className="text-sm font-medium text-ink mb-1.5">Notes</h2>
          <p className="text-sm text-ink-soft">{app.notes}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-10 mb-10">
        <PanelSection applicationId={applicationId} canManage={isRecruiter} />
        <InterviewsSection applicationId={applicationId} canSchedule={isRecruiter} />
      </div>

      <div className="mb-10">
        <FeedbackSection applicationId={applicationId} canSubmit={isAssignedInterviewer} />
      </div>

      <div>
        <h2 className="text-sm font-medium text-ink mb-4">Timeline</h2>
        <Timeline events={history ?? []} />
      </div>

      {showRejectConfirm && (
        <div
          className="fixed inset-0 z-40 flex items-center justify-center bg-ink/30"
          onClick={() => setShowRejectConfirm(false)}
        >
          <div
            className="bg-surface rounded-lg border border-line w-full max-w-sm p-6"
            onClick={(e) => e.stopPropagation()}
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="reject-confirm-title"
          >
            <h2 id="reject-confirm-title" className="font-serif text-lg text-ink mb-2">
              Reject {app.candidate_name}?
            </h2>
            <p className="text-sm text-ink-soft mb-5">
              They can be reinstated later, returning to the {app.current_stage} stage.
            </p>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setShowRejectConfirm(false)}
                className="text-sm border border-line rounded-md px-3.5 py-2 text-ink-soft"
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                disabled={reject.isPending}
                className="text-sm bg-rose text-white rounded-md px-3.5 py-2 disabled:opacity-60"
              >
                {reject.isPending ? 'Rejecting...' : 'Reject application'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
