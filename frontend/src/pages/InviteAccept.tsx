import { useEffect, useState, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '@/api/client'
import { useAuth } from '@/hooks/useAuth'
import { Coffee } from 'lucide-react'

const PENDING_INVITE_KEY = 'coffeerun_pending_invite'

export function InviteAccept() {
  const [searchParams] = useSearchParams()
  const { user, loading: authLoading, refreshUser, switchTeam } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const acceptingRef = useRef(false)

  const token = searchParams.get('token')

  useEffect(() => {
    if (authLoading || !token) return

    if (!user) {
      // Store the invite token and redirect to login
      localStorage.setItem(PENDING_INVITE_KEY, token)
      navigate('/login')
      return
    }

    // User is logged in — accept the invite
    if (acceptingRef.current) return
    acceptingRef.current = true

    api.post<{ team_id: string }>('/invites/accept', { token })
      .then(async (res) => {
        await refreshUser()
        switchTeam(res.team_id)
        navigate('/')
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to accept invite')
      })
  }, [token, user, authLoading, navigate, refreshUser, switchTeam])

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-destructive">No invite token provided</p>
          <a href="/" className="text-sm text-primary hover:underline mt-2 inline-block">Go to dashboard</a>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center">
        <Coffee className="h-8 w-8 text-primary mx-auto mb-4 animate-pulse" />
        {error ? (
          <div>
            <p className="text-destructive mb-4">{error}</p>
            <a href="/" className="text-sm text-primary hover:underline">Go to dashboard</a>
          </div>
        ) : (
          <p className="text-muted-foreground">Accepting invite...</p>
        )}
      </div>
    </div>
  )
}
