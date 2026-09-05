import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Job, JobWithCount } from '@/lib/types'

export function useJobs(includeArchived = false) {
  return useQuery<JobWithCount[]>({
    queryKey: ['jobs', { includeArchived }],
    queryFn: async () =>
      (await api.get<JobWithCount[]>('/jobs', { params: { include_archived: includeArchived } })).data,
  })
}

export function useJob(jobId: number | undefined) {
  return useQuery<Job>({
    queryKey: ['jobs', jobId],
    queryFn: async () => (await api.get<Job>(`/jobs/${jobId}`)).data,
    enabled: !!jobId,
  })
}

export function useCreateJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: { title: string; department: string; description: string }) =>
      (await api.post<Job>('/jobs', data)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  })
}

export function useUpdateJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<{ title: string; department: string; description: string }> }) =>
      (await api.patch<Job>(`/jobs/${id}`, data)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  })
}

export function useArchiveJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => (await api.post<Job>(`/jobs/${id}/archive`)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  })
}

export function useRestoreJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => (await api.post<Job>(`/jobs/${id}/restore`)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  })
}
