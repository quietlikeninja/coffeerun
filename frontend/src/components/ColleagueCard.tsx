import { type Colleague, type CoffeeOption } from '@/api/client'
import { Card } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Select } from '@/components/ui/select'

interface ColleagueCardProps {
  colleague: Colleague
  checked: boolean
  selectedOptionId: string
  onToggle: (checked: boolean) => void
  onOptionChange: (optionId: string) => void
}

function formatOption(opt: CoffeeOption): string {
  const parts: string[] = []
  if (opt.size_abbreviation) parts.push(opt.size_abbreviation)
  if (opt.milk_option_name) parts.push(opt.milk_option_name)
  if (opt.drink_type_name) parts.push(opt.drink_type_name)
  if (opt.sugar && opt.sugar > 0) parts.push(`${opt.sugar}s`)
  return parts.join(' ')
}

export function ColleagueCard({
  colleague,
  checked,
  selectedOptionId,
  onToggle,
  onOptionChange,
}: ColleagueCardProps) {
  const options = colleague.coffee_options

  return (
    <Card
      className={`p-4 transition-colors ${checked ? 'border-primary/50 bg-primary/5' : 'opacity-60'}`}
    >
      <div className="flex items-center gap-3">
        <Checkbox checked={checked} onCheckedChange={onToggle} aria-label={`Include ${colleague.name}`} />
        <div className="flex-1 min-w-0">
          <p className="font-medium truncate">{colleague.name}</p>
          {checked && options.length > 0 && (
            <div className="mt-1">
              {options.length === 1 ? (
                <p className="text-sm text-muted-foreground">{formatOption(options[0])}</p>
              ) : (
                <Select
                  value={selectedOptionId}
                  onChange={(e) => onOptionChange(e.target.value)}
                  className="h-8 py-1 text-sm"
                  aria-label={`Coffee for ${colleague.name}`}
                >
                  {options.map((opt) => (
                    <option key={opt.id} value={opt.id}>
                      {formatOption(opt)}
                    </option>
                  ))}
                </Select>
              )}
            </div>
          )}
          {checked && options.length === 0 && (
            <p className="text-sm text-muted-foreground italic">No coffee options set</p>
          )}
        </div>
      </div>
    </Card>
  )
}
