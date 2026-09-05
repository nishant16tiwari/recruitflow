import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { AlertItem } from '@/lib/types'

interface AlertListResponse {
  count: number
  alerts: AlertItem[]
}

export function useAlerts(enabled: boolean) {
  return useQuery<AlertListResponse>({
    queryKey: ['alerts'],
    queryFn: async () => (await api.get<AlertListResponse>('/alerts')).data,
    enabled,
    refetchInterval: 60_000, // badge count stays reasonably fresh without manual refresh
  })
}

export function useDismissAlert() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (applicationId: number) => {
      await api.post(`/alerts/${applicationId}/dismiss`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })
}
