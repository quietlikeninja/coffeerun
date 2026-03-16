import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from '@/context/AuthContext'
import { useAuth } from '@/hooks/useAuth'
import { Layout } from '@/components/Layout'
import { Login } from '@/pages/Login'
import { AuthVerify } from '@/pages/AuthVerify'
import { Dashboard } from '@/pages/Dashboard'
import { OrderView } from '@/pages/OrderView'
import { SharedOrder } from '@/pages/SharedOrder'
import { AdminColleagues } from '@/pages/AdminColleagues'
import { AdminMenu } from '@/pages/AdminMenu'
import { Stats } from '@/pages/Stats'
import { CreateTeam } from '@/pages/CreateTeam'
import { TeamSettings } from '@/pages/TeamSettings'
import { InviteAccept } from '@/pages/InviteAccept'
import { type ReactNode } from 'react'
import { Coffee } from 'lucide-react'

function LoadingSpinner() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <Coffee className="h-6 w-6 animate-pulse text-primary" />
    </div>
  )
}

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <LoadingSpinner />
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

function ManagerRoute({ children }: { children: ReactNode }) {
  const { isOwnerOrManager, loading, user } = useAuth()
  if (loading) return <LoadingSpinner />
  if (!user) return <Navigate to="/login" replace />
  if (!isOwnerOrManager) return <Navigate to="/" replace />
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/auth/verify" element={<AuthVerify />} />
      <Route path="/shared/:shareToken" element={<SharedOrder />} />
      <Route path="/invite" element={<InviteAccept />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout>
              <Dashboard />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/order/:id"
        element={
          <ProtectedRoute>
            <Layout>
              <OrderView />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/teams/new"
        element={
          <ProtectedRoute>
            <Layout>
              <CreateTeam />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/teams/:teamId/settings"
        element={
          <ManagerRoute>
            <Layout>
              <TeamSettings />
            </Layout>
          </ManagerRoute>
        }
      />
      <Route
        path="/stats"
        element={
          <ProtectedRoute>
            <Layout>
              <Stats />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/colleagues"
        element={
          <ManagerRoute>
            <Layout>
              <AdminColleagues />
            </Layout>
          </ManagerRoute>
        }
      />
      <Route
        path="/admin/menu"
        element={
          <ManagerRoute>
            <Layout>
              <AdminMenu />
            </Layout>
          </ManagerRoute>
        }
      />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
