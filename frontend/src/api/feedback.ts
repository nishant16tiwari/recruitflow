import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Feedback } from '@/lib/types'

export function useFeedback(applicationId: number | undefined) {
  return useQuery<Feedback[]>({
    queryKey: ['applications', applicationId, 'feedback'],
    queryFn: async () => (await api.get<Feedback[]>(`/applications/${applicationId}/feedback`)).data,
    enabled: !!applicationId,
  })
}

export function useSubmitFeedback(applicationId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (content: string) =>
      (await api.post<Feedback>(`/applications/${applicationId}/feedback`, { content })).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications', applicationId, 'feedback'] })
      queryClient.invalidateQueries({ queryKey: ['applications', applicationId, 'history'] })
    },
  })
}
