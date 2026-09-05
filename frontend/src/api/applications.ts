import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Application, BulkActionResult, PaginatedResponse, Stage } from '@/lib/types'

export interface ApplicationSearchParams {
  search?: string
  job_id?: number
  stage?: Stage
  source?: string
  sort_by?: 'applied_date' | 'stage' | 'last_updated'
  sort_order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

export function useApplicationsSearch(params: ApplicationSearchParams) {
  return useQuery<PaginatedResponse<Application>>({
    queryKey: ['applications', params],
    queryFn: async () => (await api.get<PaginatedResponse<Application>>('/applications', { params })).data,
    placeholderData: (prev) => prev, // keeps the table showing while the next page loads, instead of flashing empty
  })
}

export function useApplication(id: number | undefined) {
  return useQuery<Application>({
    queryKey: ['applications', 'detail', id],
    queryFn: async () => (await api.get<Application>(`/applications/${id}`)).data,
    enabled: !!id,
  })
}

export function useMyApplications() {
  return useQuery<Application[]>({
    queryKey: ['applications', 'my'],
    queryFn: async () => (await api.get<Application[]>('/applications/my')).data,
  })
}

export function useCreateApplication() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: {
      job_id: number
      candidate_name: string
      candidate_email: string
      source: string
      notes?: string
    }) => (await api.post<Application>('/applications', data)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] })
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    },
  })
}

function invalidateApplication(queryClient: ReturnType<typeof useQueryClient>, id: number) {
  queryClient.invalidateQueries({ queryKey: ['applications'] })
  queryClient.invalidateQueries({ queryKey: ['applications', 'detail', id] })
  queryClient.invalidateQueries({ queryKey: ['dashboard'] })
  queryClient.invalidateQueries({ queryKey: ['alerts'] })
}

export function useAdvanceApplication() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => (await api.post<Application>(`/applications/${id}/advance`, {})).data,
    onSuccess: (_, id) => invalidateApplication(queryClient, id),
  })
}

export function useRejectApplication() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, note }: { id: number; note?: string }) =>
      (await api.post<Application>(`/applications/${id}/reject`, { note: note ?? '' })).data,
    onSuccess: (_, { id }) => invalidateApplication(queryClient, id),
  })
}

export function useReinstateApplication() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => (await api.post<Application>(`/applications/${id}/reinstate`, {})).data,
    onSuccess: (_, id) => invalidateApplication(queryClient, id),
  })
}

export function useBulkAdvance() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (applicationIds: number[]) =>
      (await api.post<{ results: BulkActionResult[] }>('/applications/bulk/advance', { application_ids: applicationIds })).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })
}

export function useBulkReject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (applicationIds: number[]) =>
      (await api.post<{ results: BulkActionResult[] }>('/applications/bulk/reject', { application_ids: applicationIds })).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })
}
