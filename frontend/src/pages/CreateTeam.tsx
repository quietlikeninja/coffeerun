import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, type Team } from '@/api/client'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function CreateTeam() {
  const { refreshUser, switchTeam } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return
    setError('')
    setLoading(true)
    try {
      const team = await api.post<Team>('/teams', { name: name.trim() })
      await refreshUser()
      switchTeam(team.id)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create team')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-sm mx-auto py-8">
      <Card>
        <CardHeader>
          <CardTitle>Create a Team</CardTitle>
          <p className="text-sm text-muted-foreground">
            Give your team a name. You can change it later.
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              placeholder="e.g. Marketing, Engineering, Level 3"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
              required
              aria-label="Team name"
            />
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading || !name.trim()}>
              {loading ? 'Creating...' : 'Create Team'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
