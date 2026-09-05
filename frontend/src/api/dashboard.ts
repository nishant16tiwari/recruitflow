import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { DashboardData } from '@/lib/types'

export function useDashboard() {
  return useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: async () => (await api.get<DashboardData>('/dashboard')).data,
  })
}
