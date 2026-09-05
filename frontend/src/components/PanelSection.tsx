import { useState } from 'react'
import { X, Plus } from 'lucide-react'
import { usePanel, useAssignInterviewer, useRemoveInterviewer, useKnownInterviewers } from '@/api/panel'
import { useToast } from '@/components/Toast'
import { getErrorMessage } from '@/lib/api'

export function PanelSection({ applicationId, canManage }: { applicationId: number; canManage: boolean }) {
  const { data: panel } = usePanel(applicationId)
  const { data: interviewers } = useKnownInterviewers()
  const assign = useAssignInterviewer(applicationId)
  const remove = useRemoveInterviewer(applicationId)
  const { showToast } = useToast()
  const [picking, setPicking] = useState(false)

  const assignedIds = new Set((panel ?? []).map((p) => p.interviewer_id))
  const available = (interviewers ?? []).filter((i) => !assignedIds.has(i.id))

  function handleAssign(id: number) {
    assign.mutate(id, {
      onSuccess: () => setPicking(false),
      onError: (err) => showToast(getErrorMessage(err), 'error'),
    })
  }

  function handleRemove(id: number, name: string) {
    remove.mutate(id, {
      onSuccess: () => showToast(`${name} removed from panel`),
      onError: (err) => showToast(getErrorMessage(err), 'error'),
    })
  }

  return (
    <div>
      <h2 className="text-sm font-medium text-ink mb-3">Interview panel</h2>
      {(panel ?? []).length === 0 && <p className="text-sm text-ink-soft mb-2">No interviewers assigned yet.</p>}
      <ul className="flex flex-col gap-1.5 mb-2">
        {panel?.map((member) => (
          <li key={member.id} className="flex items-center justify-between text-sm">
            <div>
              <span className="text-ink">{member.interviewer.name}</span>
              <span className="text-ink-soft"> · {member.interviewer.email}</span>
            </div>
            {canManage && (
              <button
                onClick={() => handleRemove(member.interviewer_id, member.interviewer.name)}
                aria-label={`Remove ${member.interviewer.name}`}
                className="text-ink-soft hover:text-rose"
              >
                <X size={14} />
              </button>
            )}
          </li>
        ))}
      </ul>

      {canManage && (
        <>
          {picking ? (
            <div className="flex items-center gap-2 mt-2">
              <select
                autoFocus
                onChange={(e) => e.target.value && handleAssign(Number(e.target.value))}
                defaultValue=""
                className="text-sm rounded-md border border-line px-2 py-1.5 bg-surface"
              >
                <option value="" disabled>
                  Select interviewer...
                </option>
                {available.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.name}
                  </option>
                ))}
              </select>
              <button onClick={() => setPicking(false)} className="text-sm text-ink-soft hover:text-ink">
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => setPicking(true)}
              className="flex items-center gap-1 text-sm text-pine hover:text-pine-deep mt-1"
            >
              <Plus size={14} /> Add interviewer
            </button>
          )}
        </>
      )}
    </div>
  )
}
