import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Plus, ArrowUpDown } from 'lucide-react'
import { useApplicationsSearch, useBulkAdvance, useBulkReject } from '@/api/applications'
import type { ApplicationSearchParams } from '@/api/applications'
import { useJobs } from '@/api/jobs'
import { StageBadge } from '@/components/StageBadge'
import { NewApplicationModal } from '@/components/NewApplicationModal'
import { BulkResultsPanel } from '@/components/BulkResultsPanel'
import { useToast } from '@/components/Toast'
import { getErrorMessage } from '@/lib/api'
import type { BulkActionResult, Stage } from '@/lib/types'
import { format, parseISO } from 'date-fns'

const STAGES: Stage[] = ['Applied', 'Screening', 'Interview', 'Offer', 'Hired', 'Rejected']
const PAGE_SIZE = 20

export function ApplicationsPage() {
  const { showToast } = useToast()
  const { data: jobs } = useJobs()
  const jobLookup = new Map((jobs ?? []).map((j) => [j.id, j.title]))

  const [search, setSearch] = useState('')
  const [searchParams] = useSearchParams()
  const [jobId, setJobId] = useState<number | ''>(() => {
    const fromUrl = searchParams.get('job')
    return fromUrl ? Number(fromUrl) : ''
  })
  const [stage, setStage] = useState<Stage | ''>('')
  const [sortBy, setSortBy] = useState<ApplicationSearchParams['sort_by']>('last_updated')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [showNewModal, setShowNewModal] = useState(false)
  const [bulkResults, setBulkResults] = useState<BulkActionResult[] | null>(null)

  const { data, isLoading } = useApplicationsSearch({
    search: search || undefined,
    job_id: jobId || undefined,
    stage: stage || undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
    page,
    page_size: PAGE_SIZE,
  })

  const bulkAdvance = useBulkAdvance()
  const bulkReject = useBulkReject()

  function toggleSort(field: NonNullable<ApplicationSearchParams['sort_by']>) {
    if (sortBy === field) {
      setSortOrder((o) => (o === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortBy(field)
      setSortOrder('asc')
    }
  }

  function toggleSelect(id: number) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleSelectAll() {
    if (!data) return
    setSelected((prev) => {
      if (prev.size === data.items.length) return new Set()
      return new Set(data.items.map((a) => a.id))
    })
  }

  function runBulkAdvance() {
    bulkAdvance.mutate(Array.from(selected), {
      onSuccess: (res) => {
        setBulkResults(res.results)
        setSelected(new Set())
      },
      onError: (err) => showToast(getErrorMessage(err), 'error'),
    })
  }

  function runBulkReject() {
    bulkReject.mutate(Array.from(selected), {
      onSuccess: (res) => {
        setBulkResults(res.results)
        setSelected(new Set())
      },
      onError: (err) => showToast(getErrorMessage(err), 'error'),
    })
  }

  return (
    <div className="p-8 max-w-6xl">
      <div className="flex items-center justify-between mb-1">
        <h1 className="font-serif text-2xl text-ink">Applications</h1>
        <div className="flex items-center gap-2">
          <a
            href={`${import.meta.env.VITE_API_URL}/applications/export`}
            className="text-sm border border-line rounded-md px-3.5 py-2 text-ink-soft hover:text-ink hover:border-ink-soft"
          >
            Export CSV
          </a>
          <button
            onClick={() => setShowNewModal(true)}
            className="flex items-center gap-1.5 bg-pine hover:bg-pine-deep text-white text-sm font-medium rounded-md px-3.5 py-2"
          >
            <Plus size={16} /> New application
          </button>
        </div>
      </div>
      <p className="text-sm text-ink-soft mb-6">Every candidate across every job opening you manage.</p>

      <div className="flex flex-wrap gap-2 mb-4">
        <input
          type="text"
          placeholder="Search name or email..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setPage(1)
          }}
          className="flex-1 min-w-48 rounded-md border border-line px-3 py-2 text-sm bg-surface"
        />
        <select
          value={jobId}
          onChange={(e) => {
            setJobId(e.target.value ? Number(e.target.value) : '')
            setPage(1)
          }}
          className="rounded-md border border-line px-3 py-2 text-sm bg-surface"
        >
          <option value="">All jobs</option>
          {(jobs ?? []).map((j) => (
            <option key={j.id} value={j.id}>
              {j.title}
            </option>
          ))}
        </select>
        <select
          value={stage}
          onChange={(e) => {
            setStage((e.target.value as Stage) || '')
            setPage(1)
          }}
          className="rounded-md border border-line px-3 py-2 text-sm bg-surface"
        >
          <option value="">All stages</option>
          {STAGES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      {selected.size > 0 && (
        <div className="flex items-center gap-3 bg-pine-soft border border-pine/20 rounded-md px-4 py-2.5 mb-4">
          <span className="text-sm text-pine-deep font-medium">{selected.size} selected</span>
          <button
            onClick={runBulkAdvance}
            disabled={bulkAdvance.isPending}
            className="text-sm bg-pine text-white rounded px-3 py-1.5 hover:bg-pine-deep disabled:opacity-60"
          >
            Advance
          </button>
          <button
            onClick={runBulkReject}
            disabled={bulkReject.isPending}
            className="text-sm bg-surface border border-rose/30 text-rose rounded px-3 py-1.5 hover:bg-rose-soft disabled:opacity-60"
          >
            Reject
          </button>
          <button
            onClick={() => setSelected(new Set())}
            className="text-sm text-pine-deep/70 hover:text-pine-deep ml-auto"
          >
            Clear
          </button>
        </div>
      )}

      {bulkResults && <BulkResultsPanel results={bulkResults} onDismiss={() => setBulkResults(null)} />}

      <div className="border border-line rounded-md overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line bg-line-soft/50 text-left">
              <th className="w-10 px-4 py-2.5">
                <input
                  type="checkbox"
                  aria-label="Select all"
                  checked={!!data && data.items.length > 0 && selected.size === data.items.length}
                  onChange={toggleSelectAll}
                />
              </th>
              <th className="px-3 py-2.5 font-medium text-ink-soft">Candidate</th>
              <th className="px-3 py-2.5 font-medium text-ink-soft">Job</th>
              <th className="px-3 py-2.5 font-medium text-ink-soft">Stage</th>
              <th className="px-3 py-2.5 font-medium text-ink-soft">Source</th>
              <th className="px-3 py-2.5 font-medium text-ink-soft">
                <button onClick={() => toggleSort('applied_date')} className="flex items-center gap-1">
                  Applied <ArrowUpDown size={12} />
                </button>
              </th>
              <th className="px-3 py-2.5 font-medium text-ink-soft">
                <button onClick={() => toggleSort('last_updated')} className="flex items-center gap-1">
                  Updated <ArrowUpDown size={12} />
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-ink-soft text-sm">
                  Loading...
                </td>
              </tr>
            )}
            {!isLoading && data?.items.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-ink-soft text-sm">
                  No applications match these filters.
                </td>
              </tr>
            )}
            {data?.items.map((app) => (
              <tr key={app.id} className="border-b border-line-soft last:border-0 hover:bg-line-soft/30">
                <td className="px-4 py-2.5">
                  <input
                    type="checkbox"
                    aria-label={`Select ${app.candidate_name}`}
                    checked={selected.has(app.id)}
                    onChange={() => toggleSelect(app.id)}
                  />
                </td>
                <td className="px-3 py-2.5">
                  <Link to={`/applications/${app.id}`} className="text-ink hover:text-pine font-medium">
                    {app.candidate_name}
                  </Link>
                  <p className="text-xs text-ink-soft">{app.candidate_email}</p>
                </td>
                <td className="px-3 py-2.5 text-ink-soft">{jobLookup.get(app.job_id) ?? '—'}</td>
                <td className="px-3 py-2.5">
                  <StageBadge stage={app.current_stage} />
                </td>
                <td className="px-3 py-2.5 text-ink-soft">{app.source}</td>
                <td className="px-3 py-2.5 text-ink-soft">{format(parseISO(app.applied_date), 'MMM d, yyyy')}</td>
                <td className="px-3 py-2.5 text-ink-soft">{format(parseISO(app.updated_at), 'MMM d, yyyy')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <p className="text-sm text-ink-soft">
            {data.total} total · page {data.page} of {data.total_pages}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="text-sm border border-line rounded px-3 py-1.5 disabled:opacity-40"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
              disabled={page >= data.total_pages}
              className="text-sm border border-line rounded px-3 py-1.5 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {showNewModal && <NewApplicationModal jobs={jobs ?? []} onClose={() => setShowNewModal(false)} />}
    </div>
  )
}
