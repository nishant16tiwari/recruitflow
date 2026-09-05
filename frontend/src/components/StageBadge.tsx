import type { Stage } from '@/lib/types'

const STAGE_STYLES: Record<Stage, string> = {
  Applied: 'bg-line-soft text-ink-soft',
  Screening: 'bg-line-soft text-ink-soft',
  Interview: 'bg-pine-soft text-pine-deep',
  Offer: 'bg-pine-soft text-pine-deep',
  Hired: 'bg-pine text-white',
  Rejected: 'bg-rose-soft text-rose',
}

export function StageBadge({ stage }: { stage: Stage }) {
  return (
    <span
      className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${STAGE_STYLES[stage]}`}
    >
      {stage}
    </span>
  )
}
