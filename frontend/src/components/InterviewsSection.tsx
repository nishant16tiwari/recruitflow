import { useState } from 'react'
import { Plus, X } from 'lucide-react'
import { useApplicationInterviews, useCancelInterview } from '@/api/interviews'
import { ScheduleInterviewModal } from '@/components/ScheduleInterviewModal'
import { format, parseISO } from 'date-fns'

export function InterviewsSection({ applicationId, canSchedule }: { applicationId: number; canSchedule: boolean }) {
  const { data: interviews } = useApplicationInterviews(applicationId)
  const cancelInterview = useCancelInterview(applicationId)
  const [showModal, setShowModal] = useState(false)

  return (
    <div>
      <h2 className="text-sm font-medium text-ink mb-3">Scheduled interviews</h2>
      {(interviews ?? []).length === 0 && <p className="text-sm text-ink-soft mb-2">None scheduled yet.</p>}
      <ul className="flex flex-col gap-2.5 mb-2">
        {interviews?.map((iv) => (
          <li key={iv.id} className="text-sm flex items-start justify-between gap-3">
            <div>
              <p className="text-ink">
                {format(parseISO(iv.date), 'MMM d, yyyy')} · {iv.start_time.slice(0, 5)}–{iv.end_time.slice(0, 5)}
              </p>
              <p className="text-ink-soft">
                {iv.interview_type} · {iv.interviewers.map((i) => i.name).join(', ')}
              </p>
              {iv.meeting_link && (
                <a href={iv.meeting_link} className="text-pine hover:text-pine-deep text-xs">
                  {iv.meeting_link}
                </a>
              )}
            </div>

            {canSchedule && (
              <button
                onClick={() => cancelInterview.mutate(iv.id)}
                aria-label="Cancel interview"
                className="text-ink-soft hover:text-rose shrink-0"
              >
                <X size={15} />
              </button>
            )}
          </li>
        ))}
      </ul>

      {canSchedule && (
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1 text-sm text-pine hover:text-pine-deep mt-1"
        >
          <Plus size={14} /> Schedule interview
        </button>
      )}

      {showModal && <ScheduleInterviewModal applicationId={applicationId} onClose={() => setShowModal(false)} />}
    </div>
  )
}