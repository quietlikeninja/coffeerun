import { type ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { Coffee, BarChart3, Users, Settings, LogOut } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout, isAdmin } = useAuth()
  const location = useLocation()

  const navItems = [
    { to: '/', label: 'Order', icon: Coffee },
    { to: '/stats', label: 'Stats', icon: BarChart3 },
    ...(isAdmin
      ? [
          { to: '/admin/colleagues', label: 'People', icon: Users },
          { to: '/admin/menu', label: 'Menu', icon: Settings },
        ]
      : []),
  ]

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b bg-card sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 font-bold text-lg text-primary">
            <Coffee className="h-5 w-5" />
            CoffeeRun
          </Link>
          {user && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground hidden sm:inline">{user.email}</span>
              <Button variant="ghost" size="icon" onClick={logout} aria-label="Log out">
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 max-w-2xl mx-auto w-full px-4 py-6">{children}</main>

      {/* Bottom navigation (mobile-first) */}
      {user && (
        <nav className="border-t bg-card sticky bottom-0 z-10">
          <div className="max-w-2xl mx-auto flex justify-around">
            {navItems.map(({ to, label, icon: Icon }) => {
              const active = location.pathname === to
              return (
                <Link
                  key={to}
                  to={to}
                  className={`flex flex-col items-center gap-1 py-2 px-3 text-xs transition-colors ${
                    active ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  {label}
                </Link>
              )
            })}
          </div>
        </nav>
      )}
    </div>
  )
}
