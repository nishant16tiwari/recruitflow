import { useState } from 'react'
import { useFeedback, useSubmitFeedback } from '@/api/feedback'
import { useToast } from '@/components/Toast'
import { getErrorMessage } from '@/lib/api'
import { format, parseISO } from 'date-fns'

export function FeedbackSection({ applicationId, canSubmit }: { applicationId: number; canSubmit: boolean }) {
  const { data: feedback } = useFeedback(applicationId)
  const submit = useSubmitFeedback(applicationId)
  const { showToast } = useToast()
  const [content, setContent] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!content.trim()) return
    submit.mutate(content, {
      onSuccess: () => {
        setContent('')
        showToast('Feedback submitted')
      },
      onError: (err) => showToast(getErrorMessage(err), 'error'),
    })
  }

  return (
    <div>
      <h2 className="text-sm font-medium text-ink mb-3">Feedback</h2>
      {(feedback ?? []).length === 0 && <p className="text-sm text-ink-soft mb-2">No feedback yet.</p>}
      <ul className="flex flex-col gap-3 mb-3">
        {feedback?.map((f) => (
          <li key={f.id} className="border-l-2 border-line pl-3">
            <p className="text-sm text-ink">{f.content}</p>
            <p className="text-xs text-ink-soft mt-1">{format(parseISO(f.created_at), 'MMM d, yyyy')}</p>
          </li>
        ))}
      </ul>

      {canSubmit && (
        <form onSubmit={handleSubmit} className="flex flex-col gap-2">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Share your interview feedback..."
            rows={3}
            className="w-full rounded-md border border-line px-3 py-2 text-sm bg-surface resize-none"
          />
          <button
            type="submit"
            disabled={submit.isPending || !content.trim()}
            className="self-start text-sm bg-pine text-white rounded-md px-3.5 py-1.5 hover:bg-pine-deep disabled:opacity-60"
          >
            {submit.isPending ? 'Submitting...' : 'Submit feedback'}
          </button>
        </form>
      )}
    </div>
  )
}
