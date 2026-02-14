import { createContext, type ReactNode, useCallback, useEffect, useState } from 'react'
import { api, type User } from '@/api/client'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string) => Promise<string>
  verify: (token: string) => Promise<void>
  logout: () => Promise<void>
  isAdmin: boolean
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  login: async () => '',
  verify: async () => {},
  logout: async () => {},
  isAdmin: false,
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchUser = useCallback(async () => {
    try {
      const data = await api.get<User>('/auth/me')
      setUser(data)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  const login = async (email: string): Promise<string> => {
    const res = await api.post<{ message: string }>('/auth/login', { email })
    return res.message
  }

  const verify = async (token: string) => {
    const data = await api.post<User>('/auth/verify', { token })
    setUser(data)
  }

  const logout = async () => {
    await api.post('/auth/logout')
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        verify,
        logout,
        isAdmin: user?.role === 'admin',
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
