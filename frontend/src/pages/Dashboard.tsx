import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, type Colleague, type Order } from '@/api/client'
import { ColleagueCard } from '@/components/ColleagueCard'
import { Button } from '@/components/ui/button'
import { Coffee } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

interface Selection {
  [colleagueId: string]: {
    checked: boolean
    selectedOptionId: string
  }
}

export function Dashboard() {
  const [colleagues, setColleagues] = useState<Colleague[]>([])
  const [selection, setSelection] = useState<Selection>({})
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    api.get<Colleague[]>('/colleagues').then((data) => {
      setColleagues(data)
      const initial: Selection = {}
      for (const c of data) {
        const defaultOpt = c.coffee_options.find((o) => o.is_default) || c.coffee_options[0]
        initial[c.id] = {
          checked: c.usually_in,
          selectedOptionId: defaultOpt?.id || '',
        }
      }
      setSelection(initial)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

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
      const order = await api.post<Order>('/orders', { items })
      navigate(`/order/${order.id}`)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create order')
    } finally {
      setCreating(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Coffee className="h-6 w-6 animate-pulse text-primary" />
      </div>
    )
  }

  if (colleagues.length === 0) {
    return (
      <div className="text-center py-12">
        <Coffee className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h2 className="text-lg font-semibold mb-2">No colleagues yet</h2>
        <p className="text-muted-foreground">Ask an admin to add colleagues and their coffee preferences.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3 pb-20">
      <h1 className="text-xl font-bold">Today's Order</h1>
      <p className="text-sm text-muted-foreground">Select who's in and their coffee.</p>

      {colleagues.map((colleague) => (
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
        />
      ))}

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
    </div>
  )
}
