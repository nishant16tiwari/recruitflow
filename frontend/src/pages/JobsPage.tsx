import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Archive, ArchiveRestore, Pencil } from 'lucide-react'
import { useJobs, useArchiveJob, useRestoreJob } from '@/api/jobs'
import { JobFormModal } from '@/components/JobFormModal'
import { useToast } from '@/components/Toast'
import { getErrorMessage } from '@/lib/api'
import type { Job } from '@/lib/types'
import { format, parseISO } from 'date-fns'

export function JobsPage() {
  const [includeArchived, setIncludeArchived] = useState(false)
  const { data: jobs, isLoading } = useJobs(includeArchived)
  const archiveJob = useArchiveJob()
  const restoreJob = useRestoreJob()
  const { showToast } = useToast()

  const [modalJob, setModalJob] = useState<Job | 'new' | null>(null)

  function handleArchive(job: Job) {
    archiveJob.mutate(job.id, {
      onSuccess: () => showToast(`${job.title} archived`),
      onError: (err) => showToast(getErrorMessage(err), 'error'),
    })
  }

  function handleRestore(job: Job) {
    restoreJob.mutate(job.id, {
      onSuccess: () => showToast(`${job.title} restored`),
      onError: (err) => showToast(getErrorMessage(err), 'error'),
    })
  }

  return (
    <div className="p-8 max-w-5xl">
      <div className="flex items-center justify-between mb-1">
        <h1 className="font-serif text-2xl text-ink">Job openings</h1>
        <button
          onClick={() => setModalJob('new')}
          className="flex items-center gap-1.5 bg-pine hover:bg-pine-deep text-white text-sm font-medium rounded-md px-3.5 py-2"
        >
          <Plus size={16} /> New job opening
        </button>
      </div>
      <p className="text-sm text-ink-soft mb-6">Archiving a job hides it here but keeps every application intact.</p>

      <label className="flex items-center gap-2 text-sm text-ink-soft mb-4">
        <input
          type="checkbox"
          checked={includeArchived}
          onChange={(e) => setIncludeArchived(e.target.checked)}
        />
        Show archived openings
      </label>

      <div className="border border-line rounded-md overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line bg-line-soft/50 text-left">
              <th className="px-4 py-2.5 font-medium text-ink-soft">Title</th>
              <th className="px-3 py-2.5 font-medium text-ink-soft">Department</th>
              <th className="px-3 py-2.5 font-medium text-ink-soft">Status</th>
              <th className="px-3 py-2.5 font-medium text-ink-soft">Applications</th>
              <th className="px-3 py-2.5 font-medium text-ink-soft">Created</th>
              <th className="px-3 py-2.5 font-medium text-ink-soft">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-ink-soft">
                  Loading...
                </td>
              </tr>
            )}
            {!isLoading && jobs?.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-ink-soft">
                  No job openings yet. Create your first one to start building a pipeline.
                </td>
              </tr>
            )}
            {jobs?.map((job) => (
              <tr key={job.id} className="border-b border-line-soft last:border-0 hover:bg-line-soft/30">
                <td className="px-4 py-2.5">
                  <Link to={`/applications?job=${job.id}`} className="text-ink hover:text-pine font-medium">
                    {job.title}
                  </Link>
                </td>
                <td className="px-3 py-2.5 text-ink-soft">{job.department}</td>
                <td className="px-3 py-2.5">
                  <span
                    className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${
                      job.status === 'OPEN' ? 'bg-pine-soft text-pine-deep' : 'bg-line-soft text-ink-soft'
                    }`}
                  >
                    {job.status === 'OPEN' ? 'Open' : 'Archived'}
                  </span>
                </td>
                <td className="px-3 py-2.5 text-ink-soft">{job.application_count}</td>
                <td className="px-3 py-2.5 text-ink-soft">{format(parseISO(job.created_at), 'MMM d, yyyy')}</td>
                <td className="px-3 py-2.5">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setModalJob(job)}
                      aria-label={`Edit ${job.title}`}
                      className="text-ink-soft hover:text-ink"
                    >
                      <Pencil size={15} />
                    </button>
                    {job.status === 'OPEN' ? (
                      <button
                        onClick={() => handleArchive(job)}
                        aria-label={`Archive ${job.title}`}
                        className="text-ink-soft hover:text-amber"
                      >
                        <Archive size={15} />
                      </button>
                    ) : (
                      <button
                        onClick={() => handleRestore(job)}
                        aria-label={`Restore ${job.title}`}
                        className="text-ink-soft hover:text-pine"
                      >
                        <ArchiveRestore size={15} />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modalJob && (
        <JobFormModal job={modalJob === 'new' ? undefined : modalJob} onClose={() => setModalJob(null)} />
      )}
    </div>
  )
}
