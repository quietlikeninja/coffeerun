import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { Coffee } from 'lucide-react'

export function AuthVerify() {
  const [searchParams] = useSearchParams()
  const { verify } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')

  useEffect(() => {
    const token = searchParams.get('token')
    if (!token) {
      setError('No token provided')
      return
    }

    verify(token)
      .then(() => navigate('/'))
      .catch((err) => setError(err instanceof Error ? err.message : 'Verification failed'))
  }, [searchParams, verify, navigate])

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
