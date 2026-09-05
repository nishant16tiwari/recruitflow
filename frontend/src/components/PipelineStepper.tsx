import { PIPELINE_STAGES, type Stage } from '@/lib/types'

interface Props {
  currentStage: Stage
  previousStageBeforeRejection?: Stage | null
  size?: 'sm' | 'md'
}

export function PipelineStepper({ currentStage, previousStageBeforeRejection, size = 'md' }: Props) {
  const isRejected = currentStage === 'Rejected'
  // If rejected, show the pipeline up to (and highlighting) the stage they
  // were rejected FROM, with a Rejected marker appended - this is what
  // lets the UI communicate "Applied -> Screening -> Interview -> [Rejected]"
  // rather than losing where the candidate actually got to.
  const rejectedFromIndex = isRejected && previousStageBeforeRejection
    ? PIPELINE_STAGES.indexOf(previousStageBeforeRejection)
    : -1
  const currentIndex = isRejected ? rejectedFromIndex : PIPELINE_STAGES.indexOf(currentStage)

  const dotSize = size === 'sm' ? 'w-2 h-2' : 'w-2.5 h-2.5'
  const textSize = size === 'sm' ? 'text-xs' : 'text-sm'

  return (
    <div className="flex items-center" role="img" aria-label={`Pipeline stage: ${currentStage}`}>
      {PIPELINE_STAGES.map((stage, i) => {
        const isPast = i < currentIndex
        const isCurrent = i === currentIndex && !isRejected

        return (
          <div key={stage} className="flex items-center">
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={`rounded-full ${dotSize} ${
                  isCurrent ? 'bg-pine ring-4 ring-pine-soft' : isPast ? 'bg-pine' : 'bg-line'
                }`}
              />
              <span
                className={`${textSize} whitespace-nowrap ${
                  isCurrent ? 'text-ink font-medium' : isPast ? 'text-ink-soft' : 'text-ink-soft/50'
                }`}
              >
                {stage}
              </span>
            </div>
            {i < PIPELINE_STAGES.length - 1 && (
              <div className={`h-px w-8 md:w-12 mx-1 mb-4 ${i < currentIndex ? 'bg-pine' : 'bg-line'}`} />
            )}
          </div>
        )
      })}
      {isRejected && (
        <>
          <div className="h-px w-8 md:w-12 mx-1 mb-4 bg-rose/40" />
          <div className="flex flex-col items-center gap-1.5">
            <div className={`rounded-full ${dotSize} bg-rose ring-4 ring-rose-soft`} />
            <span className={`${textSize} text-rose font-medium whitespace-nowrap`}>Rejected</span>
          </div>
        </>
      )}
    </div>
  )
}
