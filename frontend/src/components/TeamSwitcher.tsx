import { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { ChevronDown, Check, Plus, Settings } from 'lucide-react'

export function TeamSwitcher() {
  const { user, activeTeamId, activeTeam, switchTeam } = useAuth()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  if (!user) return null

  const teams = user.teams

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 text-sm font-medium hover:text-primary transition-colors max-w-[160px]"
        aria-label="Switch team"
      >
        <span className="truncate">{activeTeam?.team_name || 'No team'}</span>
        <ChevronDown className="h-4 w-4 shrink-0" />
      </button>

      {open && (
        <div className="absolute top-full left-0 mt-1 w-56 rounded-md border bg-card shadow-lg z-50">
          <div className="py-1">
            {teams.map((team) => (
              <button
                key={team.team_id}
                onClick={() => {
                  switchTeam(team.team_id)
                  setOpen(false)
                }}
                className="flex items-center justify-between w-full px-3 py-2 text-sm hover:bg-accent transition-colors text-left"
              >
                <span className="truncate">{team.team_name}</span>
                <div className="flex items-center gap-1 shrink-0 ml-2">
                  <span className="text-xs text-muted-foreground capitalize">{team.role}</span>
                  {team.team_id === activeTeamId && (
                    <Check className="h-4 w-4 text-primary" />
                  )}
                </div>
              </button>
            ))}

            <div className="border-t my-1" />

            {activeTeamId && (
              <Link
                to={`/teams/${activeTeamId}/settings`}
                onClick={() => setOpen(false)}
                className="flex items-center gap-2 w-full px-3 py-2 text-sm hover:bg-accent transition-colors"
              >
                <Settings className="h-4 w-4" />
                Team Settings
              </Link>
            )}

            <Link
              to="/teams/new"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2 w-full px-3 py-2 text-sm hover:bg-accent transition-colors"
            >
              <Plus className="h-4 w-4" />
              Create Team
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
