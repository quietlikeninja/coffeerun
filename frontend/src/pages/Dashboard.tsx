import { useEffect, useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  type Colleague,
  type Order,
  type DrinkType,
  type Size,
  type MilkOption,
  type CoffeeOption,
} from '@/api/client'
import { useAuth } from '@/hooks/useAuth'
import { ColleagueCard } from '@/components/ColleagueCard'
import { CoffeeOptionPicker } from '@/components/CoffeeOptionPicker'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogTitle } from '@/components/ui/dialog'
import { Coffee, Plus, Star, Trash2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { NoTeams } from '@/pages/NoTeams'

interface Selection {
  [colleagueId: string]: {
    checked: boolean
    selectedOptionId: string
  }
}

export function Dashboard() {
  const { hasTeam, teamApi, activeTeamId, user, isOwnerOrManager } = useAuth()
  const [allColleagues, setAllColleagues] = useState<Colleague[]>([])
  const [selection, setSelection] = useState<Selection>({})
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const navigate = useNavigate()

  // Menu data — loaded lazily when a picker opens
  const [menuData, setMenuData] = useState<{
    drinkTypes: DrinkType[]
    sizes: Size[]
    milkOptions: MilkOption[]
  } | null>(null)
  const [menuLoading, setMenuLoading] = useState(false)

  // Add visitor flow
  const [showAddVisitor, setShowAddVisitor] = useState(false)
  const [visitorName, setVisitorName] = useState('')
  const [visitorStep, setVisitorStep] = useState<'name' | 'drink'>('name')
  const [addingVisitor, setAddingVisitor] = useState(false)
  const [newVisitorId, setNewVisitorId] = useState<string | null>(null)

  // Self-service editing
  const [editingColleagueId, setEditingColleagueId] = useState<string | null>(null)
  const [editDialogMode, setEditDialogMode] = useState<'add' | 'edit' | null>(null)
  const [editingOption, setEditingOption] = useState<CoffeeOption | null>(null)

  const fetchColleagues = () => {
    if (!hasTeam) {
      setLoading(false)
      return
    }
    setLoading(true)
    teamApi.get<Colleague[]>('/colleagues').then((data) => {
      setAllColleagues(data)
      setSelection((prev) => {
        const next: Selection = {}
        for (const c of data) {
          if (prev[c.id]) {
            // Preserve existing selection
            next[c.id] = prev[c.id]
          } else {
            const defaultOpt = c.coffee_options.find((o) => o.is_default) || c.coffee_options[0]
            next[c.id] = {
              checked: c.usually_in,
              selectedOptionId: defaultOpt?.id || '',
            }
          }
        }
        return next
      })
      setLoading(false)
    }).catch(() => setLoading(false))
  }

  useEffect(() => { fetchColleagues() }, [hasTeam, teamApi, activeTeamId]) // eslint-disable-line react-hooks/exhaustive-deps

  const fetchMenuData = async () => {
    if (menuData) return menuData
    setMenuLoading(true)
    const [dt, s, m] = await Promise.all([
      teamApi.get<DrinkType[]>('/menu/drink-types'),
      teamApi.get<Size[]>('/menu/sizes'),
      teamApi.get<MilkOption[]>('/menu/milk-options'),
    ])
    const data = { drinkTypes: dt, sizes: s, milkOptions: m }
    setMenuData(data)
    setMenuLoading(false)
    return data
  }

  // Split colleagues and visitors
  const colleagues = useMemo(
    () => allColleagues.filter((c) => c.colleague_type === 'colleague'),
    [allColleagues]
  )
  const visitors = useMemo(
    () => allColleagues.filter((c) => c.colleague_type === 'visitor'),
    [allColleagues]
  )

  if (!hasTeam && !loading) {
    return <NoTeams />
  }

  const checkedCount = Object.values(selection).filter((s) => s.checked).length

  const handleCreateOrder = async () => {
    const items = Object.entries(selection)
      .filter(([, s]) => s.checked && s.selectedOptionId)
      .map(([colleagueId, s]) => ({
        colleague_id: colleagueId,
        coffee_option_id: s.selectedOptionId,
      }))

    if (items.length === 0) return

    setCreating(true)
    try {
      const order = await teamApi.post<Order>('/orders', { items })
      navigate(`/order/${order.id}`)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create order')
    } finally {
      setCreating(false)
    }
  }

  // --- Add Visitor handlers ---
  const openAddVisitor = async () => {
    setShowAddVisitor(true)
    setVisitorName('')
    setVisitorStep('name')
    setNewVisitorId(null)
    await fetchMenuData()
  }

  const handleVisitorNameNext = async () => {
    if (!visitorName.trim()) return
    setAddingVisitor(true)
    try {
      const created = await teamApi.post<Colleague>('/colleagues', {
        name: visitorName.trim(),
        colleague_type: 'visitor',
        usually_in: false,
      })
      setNewVisitorId(created.id)
      setVisitorStep('drink')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create visitor')
    } finally {
      setAddingVisitor(false)
    }
  }

  const handleVisitorDrinkSave = async (data: {
    drink_type_id: string
    size_id: string
    milk_option_id: string | null
    sugar: number
    notes: string
    is_default: boolean
  }) => {
    if (!newVisitorId) return
    await teamApi.post(`/colleagues/${newVisitorId}/coffee-options`, { ...data, is_default: true })
    setShowAddVisitor(false)
    fetchColleagues()
  }

  // --- Self-service edit handlers ---
  const openSelfServiceEditor = async (colleagueId: string) => {
    setEditingColleagueId(colleagueId)
    await fetchMenuData()
  }

  const closeSelfServiceEditor = () => {
    setEditingColleagueId(null)
    setEditDialogMode(null)
    setEditingOption(null)
  }

  const handleSelfServiceAdd = async (data: {
    drink_type_id: string
    size_id: string
    milk_option_id: string | null
    sugar: number
    notes: string
    is_default: boolean
  }) => {
    if (!editingColleagueId) return
    await teamApi.post(`/colleagues/${editingColleagueId}/coffee-options`, data)
    setEditDialogMode(null)
    fetchColleagues()
  }

  const handleSelfServiceEdit = async (data: {
    drink_type_id: string
    size_id: string
    milk_option_id: string | null
    sugar: number
    notes: string
    is_default: boolean
  }) => {
    if (!editingOption) return
    await teamApi.put(`/coffee-options/${editingOption.id}`, data)
    setEditDialogMode(null)
    setEditingOption(null)
    fetchColleagues()
  }

  const handleSelfServiceDelete = async (optionId: string) => {
    await teamApi.delete(`/coffee-options/${optionId}`)
    fetchColleagues()
  }

  const handleSelfServiceSetDefault = async (optionId: string) => {
    await teamApi.put(`/coffee-options/${optionId}/set-default`)
    fetchColleagues()
  }

  const editingColleague = allColleagues.find((c) => c.id === editingColleagueId)

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Coffee className="h-6 w-6 animate-pulse text-primary" />
      </div>
    )
  }

  if (allColleagues.length === 0) {
    return (
      <div className="text-center py-12">
        <Coffee className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h2 className="text-lg font-semibold mb-2">No colleagues yet</h2>
        <p className="text-muted-foreground">Ask an owner or manager to add colleagues and their coffee preferences.</p>
      </div>
    )
  }

  const canEdit = (colleague: Colleague) =>
    colleague.user_id === user?.id || isOwnerOrManager

  const renderColleagueCard = (colleague: Colleague) => (
    <ColleagueCard
      key={colleague.id}
      colleague={colleague}
      checked={selection[colleague.id]?.checked || false}
      selectedOptionId={selection[colleague.id]?.selectedOptionId || ''}
      onToggle={(checked) =>
        setSelection((prev) => ({
          ...prev,
          [colleague.id]: { ...prev[colleague.id], checked },
        }))
      }
      onOptionChange={(optionId) =>
        setSelection((prev) => ({
          ...prev,
          [colleague.id]: { ...prev[colleague.id], selectedOptionId: optionId },
        }))
      }
      onEdit={canEdit(colleague) ? () => openSelfServiceEditor(colleague.id) : undefined}
    />
  )

  return (
    <div className="space-y-3 pb-20">
      <h1 className="text-xl font-bold">Today's Order</h1>
      <p className="text-sm text-muted-foreground">Select who's in and their coffee.</p>

      {/* Colleagues section */}
      {colleagues.length > 0 && (
        <div className="space-y-3">
          {colleagues.map(renderColleagueCard)}
        </div>
      )}

      {/* Visitors section */}
      {(visitors.length > 0 || isOwnerOrManager) && (
        <div className="space-y-3">
          <div className="flex items-center justify-between pt-2">
            <p className="text-sm font-medium text-muted-foreground">
              Visitors{visitors.length > 0 && ` (${visitors.length})`}
            </p>
            {isOwnerOrManager && (
              <Button size="sm" variant="outline" onClick={openAddVisitor}>
                <Plus className="h-4 w-4 mr-1" /> Add Visitor
              </Button>
            )}
          </div>
          {visitors.map(renderColleagueCard)}
        </div>
      )}

      {/* Sticky bottom button */}
      <div className="fixed bottom-16 left-0 right-0 p-4 bg-background/80 backdrop-blur border-t">
        <div className="max-w-2xl mx-auto">
          <Button
            onClick={handleCreateOrder}
            disabled={checkedCount === 0 || creating}
            className="w-full h-12 text-base"
          >
            {creating ? 'Creating...' : 'View Order'}
            {checkedCount > 0 && (
              <Badge variant="secondary" className="ml-2">{checkedCount}</Badge>
            )}
          </Button>
        </div>
      </div>

      {/* Add Visitor Dialog */}
      <Dialog open={showAddVisitor} onClose={() => setShowAddVisitor(false)}>
        <DialogTitle>Add Visitor</DialogTitle>
        {visitorStep === 'name' ? (
          <div className="space-y-4">
            <Input
              placeholder="Visitor's name"
              value={visitorName}
              onChange={(e) => setVisitorName(e.target.value)}
              autoFocus
            />
            <div className="flex gap-2">
              <Button
                onClick={handleVisitorNameNext}
                disabled={!visitorName.trim() || addingVisitor}
                className="flex-1"
              >
                {addingVisitor ? 'Creating...' : 'Next — Choose Drink'}
              </Button>
              <Button variant="outline" onClick={() => setShowAddVisitor(false)} className="flex-1">
                Cancel
              </Button>
            </div>
          </div>
        ) : menuData && !menuLoading ? (
          <CoffeeOptionPicker
            drinkTypes={menuData.drinkTypes}
            sizes={menuData.sizes}
            milkOptions={menuData.milkOptions}
            onSave={handleVisitorDrinkSave}
            onCancel={() => setShowAddVisitor(false)}
          />
        ) : (
          <p className="text-sm text-muted-foreground">Loading menu...</p>
        )}
      </Dialog>

      {/* Self-Service / Edit Drinks Dialog */}
      <Dialog open={!!editingColleagueId && !editDialogMode} onClose={closeSelfServiceEditor}>
        {editingColleague && (
          <>
            <DialogTitle>Drinks — {editingColleague.name}</DialogTitle>
            <div className="space-y-2">
              {editingColleague.coffee_options.length === 0 && (
                <p className="text-sm text-muted-foreground italic">No coffee options configured</p>
              )}
              {editingColleague.coffee_options.map((opt) => (
                <div
                  key={opt.id}
                  className="flex items-center justify-between text-sm py-2 border-b last:border-0"
                >
                  <span>
                    {opt.size_abbreviation} {opt.milk_option_name ? `${opt.milk_option_name} ` : ''}
                    {opt.drink_type_name}
                    {opt.sugar > 0 ? `, ${opt.sugar}s` : ''}
                    {opt.notes ? ` (${opt.notes})` : ''}
                  </span>
                  <div className="flex items-center gap-1">
                    {opt.is_default ? (
                      <Star className="h-3.5 w-3.5 text-primary fill-primary" />
                    ) : (
                      <button
                        onClick={() => handleSelfServiceSetDefault(opt.id)}
                        className="text-muted-foreground hover:text-primary"
                        aria-label="Set as default"
                      >
                        <Star className="h-3.5 w-3.5" />
                      </button>
                    )}
                    <button
                      onClick={() => {
                        setEditingOption(opt)
                        setEditDialogMode('edit')
                      }}
                      className="text-muted-foreground hover:text-foreground ml-1"
                      aria-label="Edit option"
                    >
                      <span className="text-xs underline">Edit</span>
                    </button>
                    <button
                      onClick={() => handleSelfServiceDelete(opt.id)}
                      className="text-muted-foreground hover:text-destructive ml-1"
                      aria-label="Delete option"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              ))}
              <Button
                size="sm"
                variant="outline"
                className="w-full mt-2"
                onClick={() => setEditDialogMode('add')}
              >
                <Plus className="h-4 w-4 mr-1" /> Add coffee option
              </Button>
            </div>
          </>
        )}
      </Dialog>

      {/* Add/Edit coffee option sub-dialog */}
      <Dialog
        open={!!editDialogMode}
        onClose={() => { setEditDialogMode(null); setEditingOption(null) }}
      >
        <DialogTitle>{editDialogMode === 'edit' ? 'Edit Coffee Option' : 'Add Coffee Option'}</DialogTitle>
        {menuData && editDialogMode === 'add' && (
          <CoffeeOptionPicker
            drinkTypes={menuData.drinkTypes}
            sizes={menuData.sizes}
            milkOptions={menuData.milkOptions}
            onSave={handleSelfServiceAdd}
            onCancel={() => setEditDialogMode(null)}
          />
        )}
        {menuData && editDialogMode === 'edit' && editingOption && (
          <CoffeeOptionPicker
            drinkTypes={menuData.drinkTypes}
            sizes={menuData.sizes}
            milkOptions={menuData.milkOptions}
            initial={{
              drink_type_id: editingOption.drink_type_id,
              size_id: editingOption.size_id,
              milk_option_id: editingOption.milk_option_id,
              sugar: editingOption.sugar,
              notes: editingOption.notes || '',
              is_default: editingOption.is_default,
            }}
            onSave={handleSelfServiceEdit}
            onCancel={() => { setEditDialogMode(null); setEditingOption(null) }}
          />
        )}
      </Dialog>
    </div>
  )
}
