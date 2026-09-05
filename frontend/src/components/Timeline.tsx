import type { HistoryEvent } from '@/lib/types'
import { format, parseISO } from 'date-fns'

const EVENT_LABELS: Record<HistoryEvent['event_type'], string> = {
  CREATED: 'Application created',
  STAGE_CHANGE: 'Stage changed',
  REJECTED: 'Rejected',
  REINSTATED: 'Reinstated',
  FEEDBACK: 'Feedback submitted',
  INTERVIEW_SCHEDULED: 'Interview scheduled',
  INTERVIEWER_ASSIGNED: 'Interviewer assigned',
  INTERVIEWER_REMOVED: 'Interviewer removed',
}

export function Timeline({ events }: { events: HistoryEvent[] }) {
  const ordered = [...events].reverse() // newest first for the timeline view

  if (ordered.length === 0) {
    return <p className="text-sm text-ink-soft">No activity yet.</p>
  }

  return (
    <ol className="relative border-l border-line ml-1.5">
      {ordered.map((event) => (
        <li key={event.id} className="mb-5 ml-4">
          <span className="absolute -left-[5px] mt-1.5 h-2.5 w-2.5 rounded-full bg-pine" />
          <p className="text-xs text-ink-soft">{format(parseISO(event.created_at), 'MMM d, yyyy · h:mm a')}</p>
          <p className="text-sm text-ink mt-0.5">
            {EVENT_LABELS[event.event_type]}
            {event.from_stage && event.to_stage && (
              <span className="text-ink-soft">
                {' '}
                ({event.from_stage} → {event.to_stage})
              </span>
            )}
          </p>
          {event.note && <p className="text-sm text-ink-soft mt-0.5">{event.note}</p>}
        </li>
      ))}
    </ol>
  )
}
