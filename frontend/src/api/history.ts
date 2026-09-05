import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { HistoryEvent } from '@/lib/types'

export function useHistory(applicationId: number | undefined) {
  return useQuery<HistoryEvent[]>({
    queryKey: ['applications', applicationId, 'history'],
    queryFn: async () => (await api.get<HistoryEvent[]>(`/applications/${applicationId}/history`)).data,
    enabled: !!applicationId,
  })
}
