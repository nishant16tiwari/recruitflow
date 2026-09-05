import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useCurrentUser, useLogin } from '@/hooks/useAuth'
import { getErrorMessage } from '@/lib/api'

export function LoginPage() {
  const { data: user } = useCurrentUser()
  const login = useLogin()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  if (user) {
    return <Navigate to={user.role === 'RECRUITER' ? '/dashboard' : '/my-interviews'} replace />
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    login.mutate({ email, password })
  }

  return (
    <div className="min-h-screen flex bg-paper">
      {/* Left dark hero panel */}
      <div className="hidden md:flex flex-col flex-1 bg-ink px-10 py-10 justify-between">
        <span className="font-serif text-xl text-white">RecruitFlow</span>

        <div>
          <h1 className="font-serif text-4xl leading-tight text-white">
            Every candidate&apos;s<br />
            path to hire,<br />
            <span className="italic text-mint">tracked and trusted.</span>
          </h1>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-lg border border-white/15 p-4">
            <span className="text-mint text-lg">&rarr;</span>
            <p className="text-white text-sm font-semibold mt-3">Track every stage</p>
            <p className="text-white/50 text-xs mt-1 leading-relaxed">
              One clear path, enforced automatically.
            </p>
          </div>
          <div className="rounded-lg border border-white/15 p-4">
            <span className="text-mint text-lg">&#8857;</span>
            <p className="text-white text-sm font-semibold mt-3">Coordinate the panel</p>
            <p className="text-white/50 text-xs mt-1 leading-relaxed">
              Assign interviewers, collect feedback.
            </p>
          </div>
          <div className="rounded-lg border border-white/15 p-4">
            <span className="text-mint text-lg">&#8635;</span>
            <p className="text-white text-sm font-semibold mt-3">Never lose the record</p>
            <p className="text-white/50 text-xs mt-1 leading-relaxed">
              A permanent history of every decision.
            </p>
          </div>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex-1 flex flex-col justify-center px-10 md:px-20 max-w-lg">
        

        <span className="font-serif text-3xl text-ink mb-1">Welcome back</span>
        <p className="text-sm text-ink-soft mb-10">Sign in to pick up your pipeline right where you left off.</p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label htmlFor="email" className="block text-sm text-ink-soft mb-1.5">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-line px-3 py-2 text-sm text-ink bg-surface focus-visible:outline-2 focus-visible:outline-mint"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm text-ink-soft mb-1.5">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md border border-line px-3 py-2 text-sm text-ink bg-surface focus-visible:outline-2 focus-visible:outline-mint"
            />
          </div>

          {login.isError && (
            <p role="alert" className="text-sm text-rose">
              {getErrorMessage(login.error)}
            </p>
          )}

          <button
            type="submit"
            disabled={login.isPending}
            className="mt-2 bg-ink hover:bg-ink/90 text-white text-sm font-medium rounded-md px-4 py-2.5 disabled:opacity-60"
          >
            {login.isPending ? 'Signing in...' : 'Sign in'}
          </button>
        </form>


      </div>
    </div>
  )
}