import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { api } from '@/api/client'
import { Coffee } from 'lucide-react'

const PENDING_INVITE_KEY = 'coffeerun_pending_invite'

export function AuthVerify() {
  const [searchParams] = useSearchParams()
  const { verify, refreshUser } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')

  const token = searchParams.get('token')

  useEffect(() => {
    if (!token) return

    verify(token)
      .then(async () => {
        // Check for pending invite token
        const pendingInvite = localStorage.getItem(PENDING_INVITE_KEY)
        if (pendingInvite) {
          localStorage.removeItem(PENDING_INVITE_KEY)
          try {
            await api.post('/invites/accept', { token: pendingInvite })
            await refreshUser()
          } catch {
            // Invite may have expired — continue to dashboard
          }
        }
        navigate('/')
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Verification failed'))
  }, [token, verify, navigate, refreshUser])

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-destructive">No token provided</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center">
        <Coffee className="h-8 w-8 text-primary mx-auto mb-4 animate-pulse" />
        {error ? (
          <p className="text-destructive">{error}</p>
        ) : (
          <p className="text-muted-foreground">Verifying your login...</p>
        )}
      </div>
    </div>
  )
}
