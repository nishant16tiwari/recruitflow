import { useState } from 'react'
import { X } from 'lucide-react'
import { useCreateApplication } from '@/api/applications'
import type { JobWithCount } from '@/lib/types'
import { getErrorMessage } from '@/lib/api'
import { useToast } from '@/components/Toast'

const SOURCES = ['LinkedIn', 'Referral', 'Website', 'Job Board', 'Career Fair', 'Other']

export function NewApplicationModal({ jobs, onClose }: { jobs: JobWithCount[]; onClose: () => void }) {
  const create = useCreateApplication()
  const { showToast } = useToast()
  const [jobId, setJobId] = useState(jobs[0]?.id ?? 0)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [source, setSource] = useState(SOURCES[0])
  const [notes, setNotes] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    create.mutate(
      { job_id: jobId, candidate_name: name, candidate_email: email, source, notes },
      {
        onSuccess: () => {
          showToast(`${name} added to the pipeline`)
          onClose()
        },
        onError: (err) => showToast(getErrorMessage(err), 'error'),
      },
    )
  }

  return (
    <div
      className="fixed inset-0 z-40 flex items-start justify-center bg-ink/30 pt-24 pb-8 overflow-y-auto"
      onClick={onClose}>
      <div
        className="bg-surface rounded-lg border border-line w-full max-w-md p-6 max-h-[calc(100vh-8rem)] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="new-app-title"
      >
        <div className="flex items-center justify-between mb-5">
          <h2 id="new-app-title" className="font-serif text-lg text-ink">
            New application
          </h2>
          <button onClick={onClose} aria-label="Close" className="text-ink-soft hover:text-ink">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
          <div>
            <label htmlFor="job" className="block text-sm text-ink-soft mb-1.5">
              Job opening
            </label>
            <select
              id="job"
              required
              value={jobId}
              onChange={(e) => setJobId(Number(e.target.value))}
              className="w-full rounded-md border border-line px-3 py-2 text-sm bg-surface"
            >
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="name" className="block text-sm text-ink-soft mb-1.5">
              Candidate name
            </label>
            <input
              id="name"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-md border border-line px-3 py-2 text-sm bg-surface"
            />
          </div>
          <div>
            <label htmlFor="email" className="block text-sm text-ink-soft mb-1.5">
              Candidate email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-line px-3 py-2 text-sm bg-surface"
            />
          </div>
          <div>
            <label htmlFor="source" className="block text-sm text-ink-soft mb-1.5">
              Source
            </label>
            <select
              id="source"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="w-full rounded-md border border-line px-3 py-2 text-sm bg-surface"
            >
              {SOURCES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="notes" className="block text-sm text-ink-soft mb-1.5">
              Notes (optional)
            </label>
            <textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              className="w-full rounded-md border border-line px-3 py-2 text-sm bg-surface resize-none"
            />
          </div>

          <button
            type="submit"
            disabled={create.isPending || jobs.length === 0}
            className="mt-2 bg-pine hover:bg-pine-deep text-white text-sm font-medium rounded-md px-4 py-2.5 disabled:opacity-60"
          >
            {create.isPending ? 'Adding...' : 'Add application'}
          </button>
          {jobs.length === 0 && (
            <p className="text-xs text-amber">Create a job opening first before adding candidates.</p>
          )}
        </form>
      </div>
    </div>
  )
}
