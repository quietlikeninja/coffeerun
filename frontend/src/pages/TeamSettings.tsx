import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, type TeamMemberDetail, type Invite, type Team } from '@/api/client'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { Dialog, DialogTitle } from '@/components/ui/dialog'
import { Trash2, UserMinus, Send } from 'lucide-react'

export function TeamSettings() {
  const { activeTeamId, activeTeam, isOwner, user, refreshUser } = useAuth()
  const navigate = useNavigate()

  const [team, setTeam] = useState<Team | null>(null)
  const [members, setMembers] = useState<TeamMemberDetail[]>([])
  const [invites, setInvites] = useState<Invite[]>([])
  const [loading, setLoading] = useState(true)

  // Team name editing
  const [editingName, setEditingName] = useState(false)
  const [teamName, setTeamName] = useState('')

  // Invite form
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('member')
  const [inviting, setInviting] = useState(false)

  // Delete confirmation
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const fetchData = async () => {
    if (!activeTeamId) return
    try {
      const [t, m, i] = await Promise.all([
        api.get<Team>(`/teams/${activeTeamId}`),
        api.get<TeamMemberDetail[]>(`/teams/${activeTeamId}/members`),
        api.get<Invite[]>(`/teams/${activeTeamId}/invites`),
      ])
      setTeam(t)
      setMembers(m)
      setInvites(i.filter((inv) => !inv.accepted))
      setTeamName(t.name)
    } catch {
      // Error fetching team data
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [activeTeamId]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleUpdateName = async () => {
    if (!teamName.trim() || !activeTeamId) return
    await api.put(`/teams/${activeTeamId}`, { name: teamName.trim() })
    setEditingName(false)
    await refreshUser()
    fetchData()
  }

  const handleChangeRole = async (memberId: string, role: string) => {
    if (!activeTeamId) return
    await api.put(`/teams/${activeTeamId}/members/${memberId}`, { role })
    fetchData()
  }

  const handleRemoveMember = async (memberId: string) => {
    if (!activeTeamId) return
    if (!confirm('Remove this member from the team?')) return
    await api.delete(`/teams/${activeTeamId}/members/${memberId}`)
    fetchData()
  }

  const handleInvite = async () => {
    if (!inviteEmail.trim() || !activeTeamId) return
    setInviting(true)
    try {
      await api.post(`/teams/${activeTeamId}/invites`, {
        email: inviteEmail.trim(),
        role: inviteRole,
      })
      setInviteEmail('')
      setInviteRole('member')
      fetchData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to send invite')
    } finally {
      setInviting(false)
    }
  }

  const handleRevokeInvite = async (inviteId: string) => {
    if (!activeTeamId) return
    await api.delete(`/teams/${activeTeamId}/invites/${inviteId}`)
    fetchData()
  }

  const handleDeleteTeam = async () => {
    if (!activeTeamId) return
    setDeleting(true)
    try {
      await api.delete(`/teams/${activeTeamId}`)
      await refreshUser()
      setShowDeleteDialog(false)
      navigate('/')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete team')
    } finally {
      setDeleting(false)
    }
  }

  if (loading) return <div className="py-8 text-center text-muted-foreground">Loading...</div>
  if (!team || !activeTeam) return <div className="py-8 text-center text-muted-foreground">Team not found.</div>

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">Team Settings</h1>

      {/* Team Name */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Team Name</CardTitle>
        </CardHeader>
        <CardContent>
          {editingName ? (
            <div className="flex gap-2">
              <Input
                value={teamName}
                onChange={(e) => setTeamName(e.target.value)}
                autoFocus
              />
              <Button size="sm" onClick={handleUpdateName}>Save</Button>
              <Button size="sm" variant="outline" onClick={() => { setEditingName(false); setTeamName(team.name) }}>
                Cancel
              </Button>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <span className="font-medium">{team.name}</span>
              {isOwner && (
                <Button size="sm" variant="outline" onClick={() => setEditingName(true)}>
                  Edit
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Members */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Members ({members.length})</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {members.map((member) => {
            const isCurrentUser = member.user_id === user?.id
            const canChangeRole = isOwner && !isCurrentUser
            const canRemove = isOwner && !isCurrentUser

            return (
              <div key={member.id} className="flex items-center justify-between py-2 border-b last:border-0">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium truncate">
                    {member.display_name || member.email}
                    {isCurrentUser && <span className="text-muted-foreground ml-1">(you)</span>}
                  </p>
                  {member.display_name && (
                    <p className="text-xs text-muted-foreground truncate">{member.email}</p>
                  )}
                </div>
                <div className="flex items-center gap-2 ml-2">
                  {canChangeRole ? (
                    <Select
                      value={member.role}
                      onChange={(e) => handleChangeRole(member.id, e.target.value)}
                      className="w-28 h-8 text-xs"
                      aria-label={`Role for ${member.email}`}
                    >
                      <option value="owner">Owner</option>
                      <option value="manager">Manager</option>
                      <option value="member">Member</option>
                    </Select>
                  ) : (
                    <span className="text-xs text-muted-foreground capitalize">{member.role}</span>
                  )}
                  {canRemove && (
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => handleRemoveMember(member.id)}
                      className="h-8 w-8 text-destructive"
                      aria-label={`Remove ${member.email}`}
                    >
                      <UserMinus className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            )
          })}
        </CardContent>
      </Card>

      {/* Invites */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Invites</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Send invite form */}
          <div className="flex gap-2">
            <Input
              type="email"
              placeholder="Email address"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              className="flex-1"
            />
            <Select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              className="w-28"
              aria-label="Invite role"
            >
              <option value="member">Member</option>
              <option value="manager">Manager</option>
            </Select>
            <Button size="sm" onClick={handleInvite} disabled={inviting || !inviteEmail.trim()}>
              <Send className="h-4 w-4 mr-1" />
              {inviting ? '...' : 'Send'}
            </Button>
          </div>

          {/* Pending invites */}
          {invites.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground uppercase">Pending</p>
              {invites.map((invite) => (
                <div key={invite.id} className="flex items-center justify-between text-sm py-1 border-b last:border-0">
                  <div>
                    <span>{invite.email}</span>
                    <span className="text-muted-foreground ml-2 capitalize">({invite.role})</span>
                  </div>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => handleRevokeInvite(invite.id)}
                    className="h-8 w-8 text-destructive"
                    aria-label={`Revoke invite for ${invite.email}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Danger Zone */}
      {isOwner && (
        <Card className="border-destructive/50">
          <CardHeader>
            <CardTitle className="text-base text-destructive">Danger Zone</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Deleting this team is permanent. All team data, members, and history will be removed.
            </p>
            <Button
              variant="destructive"
              onClick={() => setShowDeleteDialog(true)}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete Team
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Delete confirmation dialog */}
      <Dialog open={showDeleteDialog} onClose={() => setShowDeleteDialog(false)}>
        <DialogTitle>Delete Team</DialogTitle>
        <p className="text-sm text-muted-foreground mb-6">
          Are you sure you want to delete <strong>{team.name}</strong>? This action cannot be undone.
        </p>
        <div className="flex gap-2 justify-end">
          <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>Cancel</Button>
          <Button variant="destructive" onClick={handleDeleteTeam} disabled={deleting}>
            {deleting ? 'Deleting...' : 'Delete Team'}
          </Button>
        </div>
      </Dialog>
    </div>
  )
}
