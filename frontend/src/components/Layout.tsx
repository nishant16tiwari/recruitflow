import { NavLink, Outlet } from 'react-router-dom'
import { LayoutDashboard, Users, Briefcase, CalendarCheck, Bell, LogOut } from 'lucide-react'
import { useCurrentUser, useLogout } from '@/hooks/useAuth'
import { useAlerts } from '@/api/alerts'

export function Layout() {
  const { data: user } = useCurrentUser()
  const logout = useLogout()
  const isRecruiter = user?.role === 'RECRUITER'
  const { data: alertData } = useAlerts(isRecruiter)

  const navItemClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
      isActive ? 'bg-white/10 text-mint font-medium' : 'text-white/60 hover:bg-white/5 hover:text-white'
    }`

  return (
    <div className="min-h-screen flex bg-paper">
      <aside className="w-60 shrink-0 bg-ink flex flex-col">
        <div className="px-5 py-6">
          <span className="font-serif text-xl text-white">RecruitFlow</span>
          <p className="text-xs text-white/50 mt-0.5">Recruitment pipeline</p>
        </div>

        <nav className="flex-1 px-3 flex flex-col gap-1">
          {isRecruiter && (
            <>
              <NavLink to="/dashboard" className={navItemClass}>
                <LayoutDashboard size={17} /> Dashboard
              </NavLink>
              <NavLink to="/applications" className={navItemClass}>
                <Users size={17} /> Applications
              </NavLink>
              <NavLink to="/jobs" className={navItemClass}>
                <Briefcase size={17} /> Job Openings
              </NavLink>
              <NavLink to="/alerts" className={navItemClass}>
                <Bell size={17} />
                <span className="flex-1">Alerts</span>
                {!!alertData?.count && (
                  <span className="text-xs font-medium bg-amber text-white rounded-full px-1.5 py-0.5 min-w-5 text-center">
                    {alertData.count}
                  </span>
                )}
              </NavLink>
            </>
          )}
          {!isRecruiter && (
            <NavLink to="/my-interviews" className={navItemClass}>
              <CalendarCheck size={17} /> My Interviews
            </NavLink>
          )}
        </nav>

        <div className="px-3 py-4 border-t border-white/10">
          <div className="px-3 py-2 mb-1">
            <p className="text-sm text-white font-medium truncate">{user?.name}</p>
            <p className="text-xs text-white/50 truncate">{user?.email}</p>
          </div>
          <button
            onClick={() => logout.mutate()}
            className="flex items-center gap-3 px-3 py-2 rounded-md text-sm text-white/60 hover:bg-white/5 hover:text-white w-full"
          >
            <LogOut size={17} /> Log out
          </button>
        </div>
      </aside>

      <main className="flex-1 min-w-0">
        <Outlet />
      </main>
    </div>
  )
}