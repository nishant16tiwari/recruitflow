import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { useDashboard } from '@/api/dashboard'
import { format, parseISO } from 'date-fns'

function Metric({ value, label }: { value: number; label: string }) {
  return (
    <div className="flex-1 px-6 first:pl-0 py-5">
      <p className="font-serif text-4xl text-ink">{value}</p>
      <p className="text-sm text-ink-soft mt-1">{label}</p>
    </div>
  )
}

function BreakdownBar({ label, count, max }: { label: string; count: number; max: number }) {
  const pct = max > 0 ? Math.max((count / max) * 100, count > 0 ? 4 : 0) : 0
  return (
    <div className="flex items-center gap-3 py-1.5">
      <span className="text-sm text-ink-soft w-36 shrink-0 truncate">{label}</span>
      <div className="flex-1 h-2 bg-line-soft rounded-sm overflow-hidden">
        <div className="h-full bg-pine rounded-sm" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-sm text-ink w-6 text-right shrink-0">{count}</span>
    </div>
  )
}

export function DashboardPage() {
  const { data, isLoading } = useDashboard()

  if (isLoading || !data) {
    return (
      <div className="p-8">
        <p className="text-ink-soft text-sm">Loading dashboard...</p>
      </div>
    )
  }

  const maxJobCount = Math.max(...data.by_job_opening.map((j) => j.count), 1)
  const maxStageCount = Math.max(...data.by_stage.map((s) => s.count), 1)

  const chartData = data.weekly_applications.map((w) => ({
    week: format(parseISO(w.week_start), 'MMM d'),
    count: w.count,
  }))

  return (
    <div className="p-8 max-w-6xl">
      <h1 className="font-serif text-2xl text-ink mb-1">Dashboard</h1>
      <p className="text-sm text-ink-soft mb-8">A snapshot of your active recruitment pipeline.</p>

      <div className="flex divide-x divide-line border-y border-line mb-10">
        <Metric value={data.open_positions} label="Open positions" />
        <Metric value={data.active_applications} label="Active applications" />
        <Metric value={data.interviews_this_week} label="Interviews this week" />
        <Metric value={data.hires_this_month} label="Hires this month" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-10 mb-10">
        <div>
          <h2 className="text-sm font-medium text-ink mb-3">By job opening</h2>
          {data.by_job_opening.length === 0 ? (
            <p className="text-sm text-ink-soft">No job openings yet.</p>
          ) : (
            data.by_job_opening.map((j) => (
              <BreakdownBar key={j.job_id} label={j.job_title} count={j.count} max={maxJobCount} />
            ))
          )}
        </div>
        <div>
          <h2 className="text-sm font-medium text-ink mb-3">By stage</h2>
          {data.by_stage.map((s) => (
            <BreakdownBar key={s.stage} label={s.stage} count={s.count} max={maxStageCount} />
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-sm font-medium text-ink mb-3">Applications received per week</h2>
        <div className="h-56 -ml-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 10, bottom: 0, left: 0 }}>
              <CartesianGrid stroke="#EAEDEA" vertical={false} />
              <XAxis
                dataKey="week"
                tick={{ fontSize: 12, fill: '#4B534F' }}
                axisLine={{ stroke: '#DBDFDB' }}
                tickLine={false}
              />
              <YAxis
                allowDecimals={false}
                tick={{ fontSize: 12, fill: '#4B534F' }}
                axisLine={false}
                tickLine={false}
                width={28}
              />
              <Tooltip
                contentStyle={{ borderColor: '#DBDFDB', borderRadius: 6, fontSize: 13 }}
                labelStyle={{ color: '#161D1A' }}
              />
              <Line type="monotone" dataKey="count" stroke="#1F6F5C" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
