import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Interview } from '@/lib/types'

export function useApplicationInterviews(applicationId: number | undefined) {
  return useQuery<Interview[]>({
    queryKey: ['applications', applicationId, 'interviews'],
    queryFn: async () => (await api.get<Interview[]>(`/applications/${applicationId}/interviews`)).data,
    enabled: !!applicationId,
  })
}

export function useMyInterviews() {
  return useQuery<Interview[]>({
    queryKey: ['interviews', 'my'],
    queryFn: async () => (await api.get<Interview[]>('/interviews/my')).data,
  })
}

export interface ScheduleInterviewInput {
  date: string
  start_time: string
  end_time: string
  interviewer_ids: number[]
  interview_type: string
  location?: string
  meeting_link?: string
}

export function useScheduleInterview(applicationId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: ScheduleInterviewInput) =>
      (await api.post<Interview>(`/applications/${applicationId}/interviews`, data)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications', applicationId, 'interviews'] })
      queryClient.invalidateQueries({ queryKey: ['applications', applicationId, 'panel'] })
      queryClient.invalidateQueries({ queryKey: ['applications', applicationId, 'history'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}
export function useCancelInterview(applicationId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (interviewId: number) =>
      api.delete(`/applications/${applicationId}/interviews/${interviewId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications', applicationId, 'interviews'] })
      queryClient.invalidateQueries({ queryKey: ['applications', applicationId, 'history'] })
      queryClient.invalidateQueries({ queryKey: ['interviews', 'my'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}