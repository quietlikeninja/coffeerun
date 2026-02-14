import { useEffect, useState } from 'react'
import { api, type DrinkType, type Size, type MilkOption } from '@/api/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Plus, Trash2 } from 'lucide-react'

type MenuSection = 'drink-types' | 'sizes' | 'milk-options'

export function AdminMenu() {
  const [drinkTypes, setDrinkTypes] = useState<DrinkType[]>([])
  const [sizes, setSizes] = useState<Size[]>([])
  const [milkOptions, setMilkOptions] = useState<MilkOption[]>([])
  const [loading, setLoading] = useState(true)

  // Add forms
  const [adding, setAdding] = useState<MenuSection | null>(null)
  const [newName, setNewName] = useState('')
  const [newAbbr, setNewAbbr] = useState('')

  const fetchAll = async () => {
    const [dt, s, m] = await Promise.all([
      api.get<DrinkType[]>('/menu/drink-types'),
      api.get<Size[]>('/menu/sizes'),
      api.get<MilkOption[]>('/menu/milk-options'),
    ])
    setDrinkTypes(dt)
    setSizes(s)
    setMilkOptions(m)
    setLoading(false)
  }

  useEffect(() => { fetchAll() }, [])

  const handleAdd = async (section: MenuSection) => {
    if (!newName.trim()) return
    if (section === 'sizes') {
      await api.post(`/menu/${section}`, { name: newName.trim(), abbreviation: newAbbr.trim() || newName.trim().substring(0, 3) })
    } else {
      await api.post(`/menu/${section}`, { name: newName.trim() })
    }
    setAdding(null)
    setNewName('')
    setNewAbbr('')
    fetchAll()
  }

  const handleDelete = async (section: MenuSection, id: string) => {
    await api.delete(`/menu/${section}/${id}`)
    fetchAll()
  }

  if (loading) return <div className="py-8 text-center text-muted-foreground">Loading...</div>

  const renderSection = (
    title: string,
    section: MenuSection,
    items: { id: string; name: string }[],
    extra?: (item: { id: string; name: string; [key: string]: unknown }) => string
  ) => (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{title}</CardTitle>
          <Button size="sm" variant="outline" onClick={() => { setAdding(section); setNewName(''); setNewAbbr('') }}>
            <Plus className="h-4 w-4 mr-1" /> Add
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {adding === section && (
          <div className="flex gap-2 mb-3">
            <Input
              placeholder="Name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              autoFocus
              className="flex-1"
            />
            {section === 'sizes' && (
              <Input
                placeholder="Abbr"
                value={newAbbr}
                onChange={(e) => setNewAbbr(e.target.value)}
                className="w-20"
              />
            )}
            <Button size="sm" onClick={() => handleAdd(section)}>Save</Button>
            <Button size="sm" variant="outline" onClick={() => setAdding(null)}>Cancel</Button>
          </div>
        )}
        <div className="space-y-1">
          {items.map((item) => (
            <div key={item.id} className="flex items-center justify-between text-sm py-1.5 border-b last:border-0">
              <span>
                {item.name}
                {extra ? ` (${extra(item as { id: string; name: string; [key: string]: unknown })})` : ''}
              </span>
              <button
                onClick={() => handleDelete(section, item.id)}
                className="text-muted-foreground hover:text-destructive"
                aria-label={`Delete ${item.name}`}
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Menu Configuration</h1>
      {renderSection('Drink Types', 'drink-types', drinkTypes)}
      {renderSection('Sizes', 'sizes', sizes, (item) => (item as unknown as Size).abbreviation)}
      {renderSection('Milk Options', 'milk-options', milkOptions)}
    </div>
  )
}
