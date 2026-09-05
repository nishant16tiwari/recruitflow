import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { User } from '@/lib/types'

const ME_KEY = ['auth', 'me']

export function useCurrentUser() {
  return useQuery<User | null>({
    queryKey: ME_KEY,
    queryFn: async () => {
      try {
        const { data } = await api.get<User>('/auth/me')
        return data
      } catch {
        return null
      }
    },
    retry: false,
    staleTime: 5 * 60 * 1000,
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (credentials: { email: string; password: string }) => {
      const { data } = await api.post<User>('/auth/login', credentials)
      return data
    },
    onSuccess: (user) => {
      queryClient.setQueryData(ME_KEY, user)
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      await api.post('/auth/logout')
    },
    onSuccess: () => {
      queryClient.setQueryData(ME_KEY, null)
      queryClient.clear()
    },
  })
}
