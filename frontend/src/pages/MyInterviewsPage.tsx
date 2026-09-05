import { Link } from 'react-router-dom'
import { useMyInterviews } from '@/api/interviews'
import { useMyApplications } from '@/api/applications'
import { StageBadge } from '@/components/StageBadge'
import { format, parseISO } from 'date-fns'

export function MyInterviewsPage() {
  const { data: interviews, isLoading } = useMyInterviews()
  const { data: myApplications } = useMyApplications()

  const upcoming = (interviews ?? [])
    .filter((iv) => parseISO(iv.date) >= new Date(new Date().toDateString()))
    .sort((a, b) => a.date.localeCompare(b.date))
  const past = (interviews ?? [])
    .filter((iv) => parseISO(iv.date) < new Date(new Date().toDateString()))
    .sort((a, b) => b.date.localeCompare(a.date))

  return (
    <div className="p-8 max-w-3xl">
      <h1 className="font-serif text-2xl text-ink mb-1">My interviews</h1>
      <p className="text-sm text-ink-soft mb-8">Every interview and application you're assigned to.</p>

      <div className="mb-10">
        <h2 className="text-sm font-medium text-ink mb-3">My applications</h2>
        {(myApplications ?? []).length === 0 ? (
          <p className="text-sm text-ink-soft">You're not assigned to any applications yet.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {myApplications?.map((app) => (
              <li key={app.id} className="flex items-center justify-between border border-line rounded-md px-4 py-2.5">
                <Link to={`/applications/${app.id}`} className="text-sm text-ink hover:text-pine font-medium">
                  {app.candidate_name}
                </Link>
                <StageBadge stage={app.current_stage} />
              </li>
            ))}
          </ul>
        )}
      </div>

      {isLoading && <p className="text-sm text-ink-soft">Loading...</p>}

      {!isLoading && interviews?.length === 0 && (
        <div className="border border-line rounded-md px-6 py-10 text-center">
          <p className="text-sm text-ink-soft">No interviews scheduled yet.</p>
        </div>
      )}

      {upcoming.length > 0 && (
        <div className="mb-8">
          <h2 className="text-sm font-medium text-ink mb-3">Upcoming</h2>
          <ul className="flex flex-col gap-2.5">
            {upcoming.map((iv) => (
              <li key={iv.id} className="border border-line rounded-md px-4 py-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-ink font-medium">
                    {format(parseISO(iv.date), 'EEEE, MMM d')} · {iv.start_time.slice(0, 5)}–{iv.end_time.slice(0, 5)}
                  </p>
                  <Link to={`/applications/${iv.application_id}`} className="text-sm text-pine hover:text-pine-deep">
                    View candidate
                  </Link>
                </div>
                <p className="text-sm text-ink-soft mt-0.5">{iv.interview_type}</p>
                {iv.meeting_link && (
                  <a href={iv.meeting_link} className="text-xs text-pine hover:text-pine-deep">
                    {iv.meeting_link}
                  </a>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {past.length > 0 && (
        <div>
          <h2 className="text-sm font-medium text-ink mb-3">Past</h2>
          <ul className="flex flex-col gap-2.5">
            {past.map((iv) => (
              <li key={iv.id} className="border border-line-soft rounded-md px-4 py-3 opacity-70">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-ink">
                    {format(parseISO(iv.date), 'MMM d, yyyy')} · {iv.start_time.slice(0, 5)}
                  </p>
                  <Link to={`/applications/${iv.application_id}`} className="text-sm text-pine hover:text-pine-deep">
                    View candidate
                  </Link>
                </div>
                <p className="text-sm text-ink-soft mt-0.5">{iv.interview_type}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
