import { Navigate } from 'react-router-dom'
import { useCurrentUser } from '@/hooks/useAuth'
import type { UserRole } from '@/lib/types'

export function ProtectedRoute({
  children,
  requireRole,
}: {
  children: React.ReactNode
  requireRole?: UserRole
}) {
  const { data: user, isLoading } = useCurrentUser()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-paper">
        <p className="text-ink-soft text-sm">Loading...</p>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (requireRole && user.role !== requireRole) {
    return <Navigate to={user.role === 'RECRUITER' ? '/dashboard' : '/my-interviews'} replace />
  }

  return <>{children}</>
}
