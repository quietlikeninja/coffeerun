import { createContext, type ReactNode, useCallback, useEffect, useMemo, useState } from 'react'
import { api, createTeamApi, type TeamApi, type User, type TeamMembership } from '@/api/client'

const ACTIVE_TEAM_KEY = 'coffeerun_active_team_id'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string) => Promise<string>
  verify: (token: string) => Promise<User>
  logout: () => Promise<void>
  activeTeamId: string | null
  activeTeam: TeamMembership | null
  isOwner: boolean
  isManager: boolean
  isOwnerOrManager: boolean
  hasTeam: boolean
  switchTeam: (teamId: string) => void
  refreshUser: () => Promise<void>
  teamApi: TeamApi
}

// Noop team api for when no team is selected — calls will fail with a clear error
const noopTeamApi: TeamApi = {
  get: () => Promise.reject(new Error('No active team')),
  post: () => Promise.reject(new Error('No active team')),
  put: () => Promise.reject(new Error('No active team')),
  delete: () => Promise.reject(new Error('No active team')),
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  login: async () => '',
  verify: async () => ({ id: '', email: '', display_name: null, teams: [], created_at: null }),
  logout: async () => {},
  activeTeamId: null,
  activeTeam: null,
  isOwner: false,
  isManager: false,
  isOwnerOrManager: false,
  hasTeam: false,
  switchTeam: () => {},
  refreshUser: async () => {},
  teamApi: noopTeamApi,
})

function resolveActiveTeamId(teams: TeamMembership[], storedId: string | null): string | null {
  if (!teams.length) return null
  if (storedId && teams.some((t) => t.team_id === storedId)) return storedId
  return teams[0].team_id
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTeamId, setActiveTeamId] = useState<string | null>(() =>
    localStorage.getItem(ACTIVE_TEAM_KEY)
  )

  const applyTeamId = useCallback((teams: TeamMembership[], storedId: string | null) => {
    const resolved = resolveActiveTeamId(teams, storedId)
    setActiveTeamId(resolved)
    if (resolved) {
      localStorage.setItem(ACTIVE_TEAM_KEY, resolved)
    } else {
      localStorage.removeItem(ACTIVE_TEAM_KEY)
    }
    return resolved
  }, [])

  const fetchUser = useCallback(async () => {
    try {
      const data = await api.get<User>('/auth/me')
      setUser(data)
      applyTeamId(data.teams, localStorage.getItem(ACTIVE_TEAM_KEY))
    } catch {
      setUser(null)
      setActiveTeamId(null)
    } finally {
      setLoading(false)
    }
  }, [applyTeamId])

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  const login = async (email: string): Promise<string> => {
    const res = await api.post<{ message: string }>('/auth/login', { email })
    return res.message
  }

  const verify = async (token: string): Promise<User> => {
    const data = await api.post<User>('/auth/verify', { token })
    setUser(data)
    applyTeamId(data.teams, localStorage.getItem(ACTIVE_TEAM_KEY))
    return data
  }

  const logout = async () => {
    await api.post('/auth/logout')
    setUser(null)
    setActiveTeamId(null)
    localStorage.removeItem(ACTIVE_TEAM_KEY)
  }

  const switchTeam = useCallback(
    (teamId: string) => {
      if (user?.teams.some((t) => t.team_id === teamId)) {
        setActiveTeamId(teamId)
        localStorage.setItem(ACTIVE_TEAM_KEY, teamId)
      }
    },
    [user]
  )

  const activeTeam = useMemo(
    () => user?.teams.find((t) => t.team_id === activeTeamId) ?? null,
    [user, activeTeamId]
  )

  const isOwner = activeTeam?.role === 'owner'
  const isManager = activeTeam?.role === 'manager'
  const isOwnerOrManager = isOwner || isManager
  const hasTeam = activeTeamId !== null && activeTeam !== null

  const teamApi = useMemo(
    () => (activeTeamId ? createTeamApi(activeTeamId) : noopTeamApi),
    [activeTeamId]
  )

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        verify,
        logout,
        activeTeamId,
        activeTeam,
        isOwner,
        isManager,
        isOwnerOrManager,
        hasTeam,
        switchTeam,
        refreshUser: fetchUser,
        teamApi,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
