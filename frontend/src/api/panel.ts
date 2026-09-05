import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { PanelMember, User } from '@/lib/types'

export function usePanel(applicationId: number | undefined) {
  return useQuery<PanelMember[]>({
    queryKey: ['applications', applicationId, 'panel'],
    queryFn: async () => (await api.get<PanelMember[]>(`/applications/${applicationId}/interviewers`)).data,
    enabled: !!applicationId,
  })
}

export function useAssignInterviewer(applicationId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (interviewerId: number) =>
      (await api.post<PanelMember>(`/applications/${applicationId}/interviewers`, { interviewer_id: interviewerId })).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications', applicationId, 'panel'] })
      queryClient.invalidateQueries({ queryKey: ['applications', applicationId, 'history'] })
    },
  })
}

export function useRemoveInterviewer(applicationId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (interviewerId: number) => {
      await api.delete(`/applications/${applicationId}/interviewers/${interviewerId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications', applicationId, 'panel'] })
      queryClient.invalidateQueries({ queryKey: ['applications', applicationId, 'history'] })
    },
  })
}

// The recruiter-only "list interviewers" endpoint, used to populate the
// "assign to panel" and "schedule interview" pickers.
export function useKnownInterviewers() {
  return useQuery<User[]>({
    queryKey: ['known-interviewers'],
    queryFn: async () => (await api.get<User[]>('/users/interviewers')).data,
  })
}
