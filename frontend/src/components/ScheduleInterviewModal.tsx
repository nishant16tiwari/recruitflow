import { useState } from 'react'
import { X } from 'lucide-react'
import { useScheduleInterview } from '@/api/interviews'
import { useKnownInterviewers } from '@/api/panel'
import { useToast } from '@/components/Toast'
import { getErrorMessage } from '@/lib/api'

export function ScheduleInterviewModal({ applicationId, onClose }: { applicationId: number; onClose: () => void }) {
  const { data: interviewers } = useKnownInterviewers()
  const schedule = useScheduleInterview(applicationId)
  const { showToast } = useToast()

  const today = new Date().toISOString().split('T')[0]
  const [date, setDate] = useState(today)
  const [startTime, setStartTime] = useState('10:00')
  const [endTime, setEndTime] = useState('11:00')
  const [interviewerId, setInterviewerId] = useState<number | ''>('')
  const [interviewType, setInterviewType] = useState('Video Call')
  const [meetingLink, setMeetingLink] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!date) {
      showToast('Please select a date', 'error')
      return
    }
    if (!startTime || !endTime) {
      showToast('Please specify both start and end times', 'error')
      return
    }
    if (endTime <= startTime) {
      showToast('End time must be after start time', 'error')
      return
    }
    if (!interviewerId) {
      showToast('Select an interviewer', 'error')
      return
    }
    schedule.mutate(
      {
        date,
        start_time: startTime,
        end_time: endTime,
        interviewer_ids: [Number(interviewerId)],
        interview_type: interviewType,
        meeting_link: meetingLink || undefined,
      },
      {
        onSuccess: () => {
          showToast('Interview scheduled')
          onClose()
        },
        onError: (err) => showToast(getErrorMessage(err), 'error'),
      },
    )
  }

  return (
    <div className="fixed inset-0 z-40 flex items-start justify-center bg-ink/30 pt-24 pb-8 overflow-y-auto" onClick={onClose}>
      <div
        className="bg-surface rounded-lg border border-line w-full max-w-md p-6 max-h-[calc(100vh-8rem)] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="schedule-title"
      >
        <div className="flex items-center justify-between mb-5">
          <h2 id="schedule-title" className="font-serif text-lg text-ink">
            Schedule interview
          </h2>
          <button onClick={onClose} aria-label="Close" className="text-ink-soft hover:text-ink">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
          <div>
            <label htmlFor="date" className="block text-sm text-ink-soft mb-1.5">
              Date
            </label>
            <input
              id="date"
              type="date"
              required
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-full rounded-md border border-line px-3 py-2 text-sm bg-surface"
            />
          </div>
          <div className="flex gap-3">
            <div className="flex-1">
              <label htmlFor="start" className="block text-sm text-ink-soft mb-1.5">
                Start time
              </label>
              <input
                id="start"
                type="time"
                required
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="w-full rounded-md border border-line px-3 py-2 text-sm bg-surface"
              />
            </div>
            <div className="flex-1">
              <label htmlFor="end" className="block text-sm text-ink-soft mb-1.5">
                End time
              </label>
              <input
                id="end"
                type="time"
                required
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="w-full rounded-md border border-line px-3 py-2 text-sm bg-surface"
              />
            </div>
          </div>
          <div>
            <label htmlFor="interviewer" className="block text-sm text-ink-soft mb-1.5">
              Interviewer
            </label>
            <select
              id="interviewer"
              required
              value={interviewerId}
              onChange={(e) => setInterviewerId(Number(e.target.value))}
              className="w-full rounded-md border border-line px-3 py-2 text-sm bg-surface"
            >
              <option value="" disabled>
                Select interviewer...
              </option>
              {interviewers?.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="type" className="block text-sm text-ink-soft mb-1.5">
              Type
            </label>
            <select
              id="type"
              value={interviewType}
              onChange={(e) => setInterviewType(e.target.value)}
              className="w-full rounded-md border border-line px-3 py-2 text-sm bg-surface"
            >
              <option>Video Call</option>
              <option>Phone Screen</option>
              <option>Technical</option>
              <option>Onsite</option>
            </select>
          </div>
          <div>
            <label htmlFor="link" className="block text-sm text-ink-soft mb-1.5">
              Meeting link (optional)
            </label>
            <input
              id="link"
              type="url"
              value={meetingLink}
              onChange={(e) => setMeetingLink(e.target.value)}
              placeholder="https://..."
              className="w-full rounded-md border border-line px-3 py-2 text-sm bg-surface"
            />
          </div>
          <button
            type="submit"
            disabled={schedule.isPending}
            className="mt-2 bg-pine hover:bg-pine-deep text-white text-sm font-medium rounded-md px-4 py-2.5 disabled:opacity-60"
          >
            {schedule.isPending ? 'Scheduling...' : 'Schedule interview'}
          </button>
        </form>
      </div>
    </div>
  )
}
