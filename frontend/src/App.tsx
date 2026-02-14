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
import { type ReactNode } from 'react'
import { Coffee } from 'lucide-react'

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Coffee className="h-6 w-6 animate-pulse text-primary" />
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

function AdminRoute({ children }: { children: ReactNode }) {
  const { isAdmin, loading } = useAuth()
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Coffee className="h-6 w-6 animate-pulse text-primary" />
      </div>
    )
  }
  if (!isAdmin) return <Navigate to="/" replace />
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/auth/verify" element={<AuthVerify />} />
      <Route path="/shared/:shareToken" element={<SharedOrder />} />
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
          <AdminRoute>
            <Layout>
              <AdminColleagues />
            </Layout>
          </AdminRoute>
        }
      />
      <Route
        path="/admin/menu"
        element={
          <AdminRoute>
            <Layout>
              <AdminMenu />
            </Layout>
          </AdminRoute>
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
