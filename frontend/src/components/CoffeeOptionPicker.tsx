import { useState } from 'react'
import { type DrinkType, type Size, type MilkOption } from '@/api/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Label } from '@/components/ui/label'

interface CoffeeOptionPickerProps {
  drinkTypes: DrinkType[]
  sizes: Size[]
  milkOptions: MilkOption[]
  initial?: {
    drink_type_id: string
    size_id: string
    milk_option_id: string | null
    sugar: number
    notes: string
    is_default: boolean
  }
  onSave: (data: {
    drink_type_id: string
    size_id: string
    milk_option_id: string | null
    sugar: number
    notes: string
    is_default: boolean
  }) => void
  onCancel: () => void
}

export function CoffeeOptionPicker({
  drinkTypes,
  sizes,
  milkOptions,
  initial,
  onSave,
  onCancel,
}: CoffeeOptionPickerProps) {
  const [drinkTypeId, setDrinkTypeId] = useState(initial?.drink_type_id || drinkTypes[0]?.id || '')
  const [sizeId, setSizeId] = useState(initial?.size_id || sizes[0]?.id || '')
  const [milkOptionId, setMilkOptionId] = useState<string>(initial?.milk_option_id || '')
  const [sugar, setSugar] = useState(initial?.sugar ?? 0)
  const [notes, setNotes] = useState(initial?.notes || '')
  const [isDefault, setIsDefault] = useState(initial?.is_default ?? false)

  const handleSubmit = () => {
    onSave({
      drink_type_id: drinkTypeId,
      size_id: sizeId,
      milk_option_id: milkOptionId || null,
      sugar,
      notes,
      is_default: isDefault,
    })
  }

  return (
    <div className="space-y-4">
      <div>
        <Label>Drink Type</Label>
        <Select value={drinkTypeId} onChange={(e) => setDrinkTypeId(e.target.value)}>
          {drinkTypes.map((dt) => (
            <option key={dt.id} value={dt.id}>{dt.name}</option>
          ))}
        </Select>
      </div>
      <div>
        <Label>Size</Label>
        <Select value={sizeId} onChange={(e) => setSizeId(e.target.value)}>
          {sizes.map((s) => (
            <option key={s.id} value={s.id}>{s.name} ({s.abbreviation})</option>
          ))}
        </Select>
      </div>
      <div>
        <Label>Milk</Label>
        <Select value={milkOptionId} onChange={(e) => setMilkOptionId(e.target.value)}>
          <option value="">None</option>
          {milkOptions.map((m) => (
            <option key={m.id} value={m.id}>{m.name}</option>
          ))}
        </Select>
      </div>
      <div>
        <Label>Sugar</Label>
        <Input
          type="number"
          min={0}
          max={10}
          value={sugar}
          onChange={(e) => setSugar(parseInt(e.target.value) || 0)}
        />
      </div>
      <div>
        <Label>Notes</Label>
        <Input
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="e.g. extra hot, double shot"
        />
      </div>
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="is_default"
          checked={isDefault}
          onChange={(e) => setIsDefault(e.target.checked)}
          className="h-4 w-4"
        />
        <Label htmlFor="is_default">Set as default</Label>
      </div>
      <div className="flex gap-2">
        <Button onClick={handleSubmit} className="flex-1">Save</Button>
        <Button variant="outline" onClick={onCancel} className="flex-1">Cancel</Button>
      </div>
    </div>
  )
}
