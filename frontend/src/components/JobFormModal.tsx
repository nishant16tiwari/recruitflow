import { useState } from 'react'
import { X } from 'lucide-react'
import { useCreateJob, useUpdateJob } from '@/api/jobs'
import { useToast } from '@/components/Toast'
import { getErrorMessage } from '@/lib/api'
import type { Job } from '@/lib/types'

export function JobFormModal({ job, onClose }: { job?: Job; onClose: () => void }) {
  const { showToast } = useToast()
  const create = useCreateJob()
  const update = useUpdateJob()
  const [title, setTitle] = useState(job?.title ?? '')
  const [department, setDepartment] = useState(job?.department ?? '')
  const [description, setDescription] = useState(job?.description ?? '')
  const isEditing = !!job

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (isEditing) {
      update.mutate(
        { id: job.id, data: { title, department, description } },
        {
          onSuccess: () => {
            showToast('Job opening updated')
            onClose()
          },
          onError: (err) => showToast(getErrorMessage(err), 'error'),
        },
      )
    } else {
      create.mutate(
        { title, department, description },
        {
          onSuccess: () => {
            showToast('Job opening created')
            onClose()
          },
          onError: (err) => showToast(getErrorMessage(err), 'error'),
        },
      )
    }
  }

  const isPending = create.isPending || update.isPending

  return (
    <div className="fixed inset-0 z-40 flex items-start justify-center bg-ink/30 pt-24 pb-8 overflow-y-auto" onClick={onClose}>
      <div
        className="bg-surface rounded-lg border border-line w-full max-w-md p-6 max-h-[calc(100vh-8rem)] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="job-form-title"
      >
        <div className="flex items-center justify-between mb-5">
          <h2 id="job-form-title" className="font-serif text-lg text-ink">
            {isEditing ? 'Edit job opening' : 'New job opening'}
          </h2>
          <button onClick={onClose} aria-label="Close" className="text-ink-soft hover:text-ink">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
          <div>
            <label htmlFor="title" className="block text-sm text-ink-soft mb-1.5">
              Title
            </label>
            <input
              id="title"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-md border border-line px-3 py-2 text-sm bg-surface"
            />
          </div>
          <div>
            <label htmlFor="department" className="block text-sm text-ink-soft mb-1.5">
              Department
            </label>
            <input
              id="department"
              required
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="w-full rounded-md border border-line px-3 py-2 text-sm bg-surface"
            />
          </div>
          <div>
            <label htmlFor="description" className="block text-sm text-ink-soft mb-1.5">
              Description
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full rounded-md border border-line px-3 py-2 text-sm bg-surface resize-none"
            />
          </div>
          <button
            type="submit"
            disabled={isPending}
            className="mt-2 bg-pine hover:bg-pine-deep text-white text-sm font-medium rounded-md px-4 py-2.5 disabled:opacity-60"
          >
            {isPending ? 'Saving...' : isEditing ? 'Save changes' : 'Create job opening'}
          </button>
        </form>
      </div>
    </div>
  )
}
