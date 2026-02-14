import { useEffect, useState } from 'react'
import {
  api,
  type Colleague,
  type DrinkType,
  type Size,
  type MilkOption,
} from '@/api/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogTitle } from '@/components/ui/dialog'
import { CoffeeOptionPicker } from '@/components/CoffeeOptionPicker'
import { Label } from '@/components/ui/label'
import { Plus, Trash2, Star, Pencil } from 'lucide-react'

export function AdminColleagues() {
  const [colleagues, setColleagues] = useState<Colleague[]>([])
  const [drinkTypes, setDrinkTypes] = useState<DrinkType[]>([])
  const [sizes, setSizes] = useState<Size[]>([])
  const [milkOptions, setMilkOptions] = useState<MilkOption[]>([])
  const [loading, setLoading] = useState(true)

  // New colleague form
  const [showNewForm, setShowNewForm] = useState(false)
  const [newName, setNewName] = useState('')
  const [newUsuallyIn, setNewUsuallyIn] = useState(true)

  // Edit colleague
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editName, setEditName] = useState('')

  // Coffee option dialog
  const [coffeeDialogFor, setCoffeeDialogFor] = useState<string | null>(null)

  const fetchAll = async () => {
    const [c, dt, s, m] = await Promise.all([
      api.get<Colleague[]>('/colleagues'),
      api.get<DrinkType[]>('/menu/drink-types'),
      api.get<Size[]>('/menu/sizes'),
      api.get<MilkOption[]>('/menu/milk-options'),
    ])
    setColleagues(c)
    setDrinkTypes(dt)
    setSizes(s)
    setMilkOptions(m)
    setLoading(false)
  }

  useEffect(() => { fetchAll() }, [])

  const handleCreateColleague = async () => {
    if (!newName.trim()) return
    await api.post('/colleagues', { name: newName.trim(), usually_in: newUsuallyIn })
    setNewName('')
    setShowNewForm(false)
    fetchAll()
  }

  const handleUpdateColleague = async (id: string) => {
    if (!editName.trim()) return
    await api.put(`/colleagues/${id}`, { name: editName.trim() })
    setEditingId(null)
    fetchAll()
  }

  const handleDeleteColleague = async (id: string) => {
    if (!confirm('Deactivate this colleague?')) return
    await api.delete(`/colleagues/${id}`)
    fetchAll()
  }

  const handleToggleUsuallyIn = async (id: string, usually_in: boolean) => {
    await api.put(`/colleagues/${id}`, { usually_in })
    fetchAll()
  }

  const handleAddCoffeeOption = async (colleagueId: string, data: {
    drink_type_id: string
    size_id: string
    milk_option_id: string | null
    sugar: number
    notes: string
    is_default: boolean
  }) => {
    await api.post(`/colleagues/${colleagueId}/coffee-options`, data)
    setCoffeeDialogFor(null)
    fetchAll()
  }

  const handleDeleteOption = async (optionId: string) => {
    await api.delete(`/coffee-options/${optionId}`)
    fetchAll()
  }

  const handleSetDefault = async (optionId: string) => {
    await api.put(`/coffee-options/${optionId}/set-default`)
    fetchAll()
  }

  if (loading) return <div className="py-8 text-center text-muted-foreground">Loading...</div>

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Manage Colleagues</h1>
        <Button size="sm" onClick={() => setShowNewForm(true)}>
          <Plus className="h-4 w-4 mr-1" /> Add
        </Button>
      </div>

      {showNewForm && (
        <Card>
          <CardContent className="pt-4 space-y-3">
            <Input
              placeholder="Name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              autoFocus
            />
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={newUsuallyIn}
                onChange={(e) => setNewUsuallyIn(e.target.checked)}
                id="usually_in"
              />
              <Label htmlFor="usually_in">Usually in the office</Label>
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={handleCreateColleague}>Save</Button>
              <Button size="sm" variant="outline" onClick={() => setShowNewForm(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {colleagues.map((colleague) => (
        <Card key={colleague.id}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              {editingId === colleague.id ? (
                <div className="flex gap-2 flex-1 mr-2">
                  <Input
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    className="h-8"
                    autoFocus
                  />
                  <Button size="sm" onClick={() => handleUpdateColleague(colleague.id)}>Save</Button>
                  <Button size="sm" variant="outline" onClick={() => setEditingId(null)}>Cancel</Button>
                </div>
              ) : (
                <CardTitle className="flex items-center gap-2">
                  {colleague.name}
                  <button
                    onClick={() => { setEditingId(colleague.id); setEditName(colleague.name) }}
                    className="text-muted-foreground hover:text-foreground"
                    aria-label="Edit name"
                  >
                    <Pencil className="h-3.5 w-3.5" />
                  </button>
                </CardTitle>
              )}
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-1 text-xs text-muted-foreground">
                  <input
                    type="checkbox"
                    checked={colleague.usually_in}
                    onChange={(e) => handleToggleUsuallyIn(colleague.id, e.target.checked)}
                  />
                  Usually in
                </label>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => handleDeleteColleague(colleague.id)}
                  className="h-8 w-8 text-destructive"
                  aria-label="Delete colleague"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {colleague.coffee_options.length > 0 ? (
              <div className="space-y-1">
                {colleague.coffee_options.map((opt) => (
                  <div
                    key={opt.id}
                    className="flex items-center justify-between text-sm py-1 border-b last:border-0"
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
                          onClick={() => handleSetDefault(opt.id)}
                          className="text-muted-foreground hover:text-primary"
                          aria-label="Set as default"
                        >
                          <Star className="h-3.5 w-3.5" />
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteOption(opt.id)}
                        className="text-muted-foreground hover:text-destructive"
                        aria-label="Delete option"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground italic">No coffee options configured</p>
            )}
            <Button
              size="sm"
              variant="ghost"
              className="mt-2"
              onClick={() => setCoffeeDialogFor(colleague.id)}
            >
              <Plus className="h-3.5 w-3.5 mr-1" /> Add coffee option
            </Button>
          </CardContent>
        </Card>
      ))}

      {/* Add Coffee Option Dialog */}
      <Dialog open={!!coffeeDialogFor} onClose={() => setCoffeeDialogFor(null)}>
        <DialogTitle>Add Coffee Option</DialogTitle>
        {coffeeDialogFor && (
          <CoffeeOptionPicker
            drinkTypes={drinkTypes}
            sizes={sizes}
            milkOptions={milkOptions}
            onSave={(data) => handleAddCoffeeOption(coffeeDialogFor, data)}
            onCancel={() => setCoffeeDialogFor(null)}
          />
        )}
      </Dialog>
    </div>
  )
}
